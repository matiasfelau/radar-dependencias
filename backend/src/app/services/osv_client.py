from __future__ import annotations

import logging
import math
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
            value = str(item.get("score", "")).strip()
            upper_value = value.upper()
            if "CRITICAL" in upper_value:
                return "Critical"
            if "HIGH" in upper_value:
                return "High"
            if "MEDIUM" in upper_value:
                return "Medium"
            if "LOW" in upper_value:
                return "Low"

            cvss_severity = _severity_from_cvss_vector(value)
            if cvss_severity != "Unknown":
                return cvss_severity

    database_specific = vuln.get("database_specific")
    if isinstance(database_specific, dict):
        level = str(database_specific.get("severity", "")).strip().capitalize()
        if level in {"Critical", "High", "Medium", "Low"}:
            return level

    return "Unknown"


def _severity_from_cvss_vector(vector: str) -> str:
    if not vector.startswith("CVSS:"):
        return "Unknown"

    metrics = _parse_cvss_vector(vector)
    if not metrics:
        return "Unknown"

    scope = metrics.get("S", "U")
    av = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}.get(metrics.get("AV", ""))
    ac = {"L": 0.77, "H": 0.44}.get(metrics.get("AC", ""))
    ui = {"N": 0.85, "R": 0.62}.get(metrics.get("UI", ""))

    if scope == "U":
        pr = {"N": 0.85, "L": 0.62, "H": 0.27}.get(metrics.get("PR", ""))
    else:
        pr = {"N": 0.85, "L": 0.68, "H": 0.5}.get(metrics.get("PR", ""))

    c = {"N": 0.0, "L": 0.22, "H": 0.56}.get(metrics.get("C", ""))
    i = {"N": 0.0, "L": 0.22, "H": 0.56}.get(metrics.get("I", ""))
    a = {"N": 0.0, "L": 0.22, "H": 0.56}.get(metrics.get("A", ""))

    if None in {av, ac, pr, ui, c, i, a}:
        return "Unknown"

    exploitability = 8.22 * av * ac * pr * ui
    impact_subscore = 1 - ((1 - c) * (1 - i) * (1 - a))

    if scope == "U":
        impact = 6.42 * impact_subscore
    else:
        impact = 7.52 * (impact_subscore - 0.029) - 3.25 * ((impact_subscore - 0.02) ** 15)

    if impact <= 0:
        base_score = 0.0
    else:
        base_score = min(impact + exploitability, 10.0)
        base_score = math.ceil(base_score * 10) / 10

    if base_score >= 9.0:
        return "Critical"
    if base_score >= 7.0:
        return "High"
    if base_score >= 4.0:
        return "Medium"
    if base_score > 0:
        return "Low"
    return "Unknown"


def _parse_cvss_vector(vector: str) -> dict[str, str]:
    parts = vector.split("/")
    if not parts:
        return {}

    metrics: dict[str, str] = {}
    for part in parts[1:]:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        metrics[key] = value
    return metrics
