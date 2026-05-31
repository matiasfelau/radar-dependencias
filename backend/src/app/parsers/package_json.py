from __future__ import annotations

import json
from json import JSONDecodeError

from app.parsers.base import DependencyEcosystem, DependencyParser, ParsedDependency
from app.services.npm_client import normalize_npm_version


class PackageJSONParser(DependencyParser):
    def parse(self, content: bytes) -> list[ParsedDependency]:
        try:
            payload = json.loads(content.decode("utf-8"))
        except JSONDecodeError as exc:
            raise ValueError("Invalid package.json content") from exc

        if not isinstance(payload, dict):
            raise ValueError("Invalid package.json structure")

        merged: dict[str, str] = {}
        for section in ("dependencies", "devDependencies"):
            section_payload = payload.get(section, {})
            if not isinstance(section_payload, dict):
                continue

            for package_name, version in section_payload.items():
                if isinstance(package_name, str) and isinstance(version, str):
                    normalized_version = normalize_npm_version(version)
                    merged[package_name.lower()] = normalized_version or "unspecified"

        return [
            ParsedDependency(
                package_name=package_name,
                installed_version=installed_version,
                ecosystem=DependencyEcosystem.NPM,
            )
            for package_name, installed_version in sorted(merged.items())
        ]
