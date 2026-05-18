from __future__ import annotations

import logging

import httpx
from packaging.version import InvalidVersion, Version

PYPI_JSON_URL = "https://pypi.org/pypi/{package_name}/json"
logger = logging.getLogger(__name__)


def get_latest_pypi_version(package_name: str) -> str | None:
    normalized = package_name.strip().lower()
    if not normalized:
        return None

    url = PYPI_JSON_URL.format(package_name=normalized)
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url)
            if response.status_code == 404:
                logger.debug("PyPI package not found: %s", normalized)
                return None
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("PyPI query failed for %s: %s", normalized, exc)
        return None

    body = response.json()
    if not isinstance(body, dict):
        return None

    info = body.get("info")
    if not isinstance(info, dict):
        return None

    latest_version = str(info.get("version") or "").strip()
    if not latest_version:
        return None

    try:
        Version(latest_version)
    except InvalidVersion:
        logger.debug("PyPI returned invalid latest version for %s: %s", normalized, latest_version)
        return None

    return latest_version


def has_pypi_update(installed_version: str, latest_version: str | None) -> bool:
    if not latest_version:
        return False

    try:
        current = Version(installed_version.strip())
        latest = Version(latest_version.strip())
    except InvalidVersion:
        return False

    return latest > current
