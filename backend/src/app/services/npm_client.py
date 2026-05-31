from __future__ import annotations

import logging
import re
from urllib.parse import quote

import httpx
from packaging.version import InvalidVersion, Version

NPM_REGISTRY_URL = "https://registry.npmjs.org/{package_name}"
SEMVER_EXTRACTOR = re.compile(r"(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)")
logger = logging.getLogger(__name__)


def normalize_npm_version(raw_version: str) -> str:
    candidate = raw_version.strip().lstrip("^~>=< ")
    match = SEMVER_EXTRACTOR.search(candidate)
    return match.group(1) if match else candidate


def get_latest_npm_version(package_name: str) -> str | None:
    normalized = package_name.strip()
    if not normalized:
        return None

    url = NPM_REGISTRY_URL.format(package_name=quote(normalized, safe="@/"))
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url)
            if response.status_code == 404:
                logger.debug("npm package not found: %s", normalized)
                return None
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("npm query failed for %s: %s", normalized, exc)
        return None

    body = response.json()
    if not isinstance(body, dict):
        return None

    dist_tags = body.get("dist-tags")
    if not isinstance(dist_tags, dict):
        return None

    latest_version = str(dist_tags.get("latest") or "").strip()
    if not latest_version:
        return None

    normalized_latest = normalize_npm_version(latest_version)
    try:
        Version(normalized_latest)
    except InvalidVersion:
        logger.debug("npm returned invalid latest version for %s: %s", normalized, latest_version)
        return None

    return normalized_latest


def has_npm_update(installed_version: str, latest_version: str | None) -> bool:
    if not latest_version:
        return False

    try:
        current = Version(normalize_npm_version(installed_version))
        latest = Version(normalize_npm_version(latest_version))
    except InvalidVersion:
        return False

    return latest > current