from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
VERSION_PREFIXES = ("===", "==", "~=", "!=", "<=", ">=", "<", ">", "^", "~")
logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class OSVVulnerability:
    cve_id: str
    summary: str
    severity: str
    fixed_version: str | None = None


def normalize_version_for_osv(version: str) -> str:
    cleaned = version.strip()
    for prefix in VERSION_PREFIXES:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break

    # npm style ranges like 1.2.3 || 1.2.4 are not point versions for OSV query.
    if "||" in cleaned or " " in cleaned:
        return ""

    return cleaned


def query_osv(package_name: str, installed_version: str) -> list[OSVVulnerability]:
    version = normalize_version_for_osv(installed_version)
    if not version:
        return []

    # Use the PyPI ecosystem and normalize name to lowercase for OSV queries
    payload = {"package": {"ecosystem": "PyPI", "name": package_name.lower()}, "version": version}
    try:
        logger.debug("OSV query payload for %s@%s: %s", package_name, installed_version, payload)
        with httpx.Client(timeout=15.0) as client:
            response = client.post(OSV_QUERY_URL, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("OSV query failed for %s@%s: %s", package_name, installed_version, exc)
        return []

    body = response.json()
    vulns = body.get("vulns", []) if isinstance(body, dict) else []
    if not isinstance(vulns, list):
        return []

    findings: list[OSVVulnerability] = []
    for item in vulns:
        if not isinstance(item, dict):
            continue
        # Prefer CVE aliases when present (OSV uses 'aliases' to list CVE identifiers)
        cve_id = ""
        aliases = item.get("aliases") or []
        if isinstance(aliases, list):
            for a in aliases:
                if isinstance(a, str) and a.upper().startswith("CVE-"):
                    cve_id = a.strip().upper()
                    break

        if not cve_id:
            id_val = str(item.get("id", "")).strip()
            if id_val:
                if id_val.upper().startswith("CVE-"):
                    cve_id = id_val.upper()
                else:
                    # fallback to whatever id is available
                    cve_id = id_val

        if not cve_id:
            continue

        summary = str(item.get("summary") or item.get("details") or "No description provided")
        severity = _extract_severity(item)

        # Attempt to extract the first fixed version from 'affected' ranges
        fixed_version: str | None = None
        affected = item.get("affected") or []
        if isinstance(affected, list):
            for a in affected:
                ranges = a.get("ranges") or []
                if isinstance(ranges, list):
                    for r in ranges:
                        events = r.get("events") or []
                        if isinstance(events, list):
                            for ev in events:
                                if isinstance(ev, dict) and ev.get("fixed"):
                                    fixed_version = str(ev.get("fixed"))
                                    break
                            if fixed_version:
                                break
                if fixed_version:
                    break

        findings.append(
            OSVVulnerability(cve_id=cve_id, summary=summary, severity=severity, fixed_version=fixed_version)
        )

    if findings:
        logger.debug(
            "OSV found %d vulnerabilities for %s@%s: %s",
            len(findings),
            package_name,
            installed_version,
            [f.cve_id for f in findings],
        )

    return findings


def _extract_severity(vuln: dict[str, object]) -> str:
    severity_items = vuln.get("severity", [])
    if isinstance(severity_items, list):
        for item in severity_items:
            if not isinstance(item, dict):
                continue
            value = str(item.get("score", "")).upper()
            if "CRITICAL" in value:
                return "Critical"
            if "HIGH" in value:
                return "High"
            if "MEDIUM" in value:
                return "Medium"
            if "LOW" in value:
                return "Low"

    database_specific = vuln.get("database_specific")
    if isinstance(database_specific, dict):
        level = str(database_specific.get("severity", "")).strip().capitalize()
        if level in {"Critical", "High", "Medium", "Low"}:
            return level

    return "Unknown"
