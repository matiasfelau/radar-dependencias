import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dependency import Dependency
from app.models.environment import Environment
from app.models.project import Project
from app.models.vulnerability import SeverityLevel, Vulnerability, VulnerabilityStatus
from app.schemas.projects import ActiveAlertItem, ActiveAlertsResponse
from app.services.pypi_client import get_latest_pypi_version, has_pypi_update
from app.services.vulnerability_scanner import scan_vulnerabilities

router = APIRouter(prefix="/alerts")
logger = logging.getLogger(__name__)


@router.get("/active", response_model=ActiveAlertsResponse, summary="List active vulnerability alerts")
def list_active_alerts(db: Session = Depends(get_db)) -> ActiveAlertsResponse:
    records = db.execute(
        select(Dependency, Project.name, Environment.name, Environment.updated_at, Vulnerability)
        .join(Environment, Environment.id == Dependency.environment_id)
        .join(Project, Project.id == Environment.project_id)
        .outerjoin(
            Vulnerability,
            and_(
                Vulnerability.package_name == Dependency.package_name,
                Vulnerability.affected_version == Dependency.installed_version,
                Vulnerability.status == VulnerabilityStatus.ACTIVE,
            ),
        )
        .order_by(Project.name, Environment.name, Dependency.package_name, Dependency.installed_version)
    ).all()
    
    logger.debug("Query returned %d rows total from alerts JOIN", len(records))
    for dep, proj, env, _, vuln in records:
        if vuln is not None:
            logger.debug("  Row: %s@%s in %s/%s has CVE %s", dep.package_name, dep.installed_version, proj, env, vuln.cve_id)

    latest_version_cache: dict[str, str | None] = {}
    aggregated: dict[tuple[str, str, str, str], dict[str, object]] = {}
    severity_rank = {
        SeverityLevel.UNKNOWN.value: 0,
        SeverityLevel.LOW.value: 1,
        SeverityLevel.MEDIUM.value: 2,
        SeverityLevel.HIGH.value: 3,
        SeverityLevel.CRITICAL.value: 4,
    }

    for dependency, project_name, environment_name, environment_updated_at, vulnerability in records:
        key = (project_name, environment_name, dependency.package_name, dependency.installed_version)
        if key not in aggregated:
            if dependency.package_name not in latest_version_cache:
                latest_version_cache[dependency.package_name] = get_latest_pypi_version(dependency.package_name)

            latest_version = latest_version_cache[dependency.package_name]
            aggregated[key] = {
                "project_name": project_name,
                "environment_name": environment_name,
                "package_name": dependency.package_name,
                "installed_version": dependency.installed_version,
                "has_vulnerability": False,
                "has_update": has_pypi_update(dependency.installed_version, latest_version),
                "latest_version": latest_version,
                "max_severity": None,
                "updated_at": environment_updated_at,
            }

        entry = aggregated[key]
        if vulnerability is not None:
            entry["has_vulnerability"] = True
            current_severity = vulnerability.severity.value if vulnerability.severity else SeverityLevel.UNKNOWN.value
            logger.debug("Setting has_vulnerability=True for %s@%s (CVE: %s, severity: %s)", dependency.package_name, dependency.installed_version, vulnerability.cve_id, current_severity)
            if entry["max_severity"] is None or severity_rank[current_severity] > severity_rank[str(entry["max_severity"])]:
                entry["max_severity"] = current_severity
            detected_at = getattr(vulnerability, "detected_at", None)
            if isinstance(detected_at, datetime):
                current_updated_at = entry["updated_at"]
                if not isinstance(current_updated_at, datetime) or detected_at > current_updated_at:
                    entry["updated_at"] = detected_at

    items = [
        ActiveAlertItem(
            project_name=item["project_name"],
            environment_name=item["environment_name"],
            package_name=item["package_name"],
            installed_version=item["installed_version"],
            has_vulnerability=item["has_vulnerability"],
            has_update=item["has_update"],
            latest_version=item["latest_version"],
            max_severity=item["max_severity"],
            updated_at=item["updated_at"] or datetime.now(UTC),
        )
        for item in aggregated.values()
        if item["has_vulnerability"] or item["has_update"]
    ]

    items.sort(
        key=lambda item: (
            not item.has_vulnerability,
            not item.has_update,
            item.updated_at,
        ),
        reverse=False,
    )

    logger.info("Returning %s active alerts to frontend", len(items))
    return ActiveAlertsResponse(total=len(items), items=items)


@router.post("/debug/scan", summary="Manually trigger vulnerability scan (debug only)")
def debug_trigger_scan(db: Session = Depends(get_db)) -> dict[str, int]:
    """
    Manually execute the vulnerability scanner.
    Useful for testing. In production, the background scheduler handles this.
    """
    result = scan_vulnerabilities(db)
    logger.info(
        "Manual vulnerability scan triggered from API: upserted=%s deleted=%s vulnerable=%s with_updates=%s scanned_pairs=%s",
        result.get("upserted"),
        result.get("deleted"),
        result.get("vulnerable"),
        result.get("with_updates"),
        result.get("scanned_pairs"),
    )
    return result


@router.get("/debug/vulnerabilities", summary="Debug: List all vulnerabilities in database")
def debug_list_vulnerabilities(db: Session = Depends(get_db)) -> dict[str, object]:
    """
    Show all vulnerabilities currently in the database.
    Useful for debugging why vulnerabilities aren't appearing in alerts.
    """
    vulns = db.scalars(
        select(Vulnerability)
        .order_by(Vulnerability.package_name, Vulnerability.affected_version, Vulnerability.cve_id)
    ).all()
    
    result = {
        "total": len(vulns),
        "vulnerabilities": [
            {
                "cve_id": v.cve_id,
                "package_name": v.package_name,
                "affected_version": v.affected_version,
                "severity": v.severity.value if v.severity else None,
                "status": v.status.value if v.status else None,
                "detected_at": v.detected_at.isoformat() if v.detected_at else None,
            }
            for v in vulns
        ]
    }
    logger.debug("Debug endpoint: Found %d vulnerabilities in database", len(vulns))
    for v in vulns:
        logger.debug("  CVE: %s for %s@%s (status=%s)", v.cve_id, v.package_name, v.affected_version, v.status.value if v.status else None)
    return result
