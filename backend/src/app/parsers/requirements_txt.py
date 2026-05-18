from __future__ import annotations

import re
from collections.abc import Iterable

from packaging.requirements import InvalidRequirement, Requirement

from app.parsers.base import DependencyParser, ParsedDependency

OPERATOR_PATTERN = re.compile(r"(==|~=|!=|<=|>=|<|>|===)")


class RequirementsTxtParser(DependencyParser):
    def parse(self, content: bytes) -> list[ParsedDependency]:
        text = content.decode("utf-8")
        dependencies: dict[str, str] = {}

        for raw_line in text.splitlines():
            normalized = self._normalize_line(raw_line)
            if not normalized:
                continue

            name, version = self._extract(normalized)
            dependencies[name.lower()] = version

        return [
            ParsedDependency(package_name=package_name, installed_version=installed_version)
            for package_name, installed_version in sorted(dependencies.items())
        ]

    @staticmethod
    def _normalize_line(raw_line: str) -> str:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            return ""

        hash_index = line.find(" #")
        if hash_index != -1:
            line = line[:hash_index].strip()

        if line.startswith(("-r", "--requirement", "-c", "--constraint", "-e", "--editable")):
            return ""

        return line

    def _extract(self, candidate: str) -> tuple[str, str]:
        try:
            req = Requirement(candidate)
            operator, version = self._pick_version(req.specifier)
            normalized_name = req.name.lower()
            if req.extras:
                extras = ",".join(sorted(req.extras))
                normalized_name = f"{normalized_name}[{extras}]"
                
            # ❌ ANTES: installed_version = f"{operator}{version}" if operator and version else "unspecified"
            #  AHORA: Guardamos solo la versión limpia (sin el '==')
            installed_version = version if version else "unspecified"
            return normalized_name, installed_version
        except InvalidRequirement:
            return self._fallback_extract(candidate)

    @staticmethod
    def _pick_version(specifier: Iterable[object]) -> tuple[str, str]:
        for item in specifier:
            operator = getattr(item, "operator", "")
            version = getattr(item, "version", "")
            if operator and version:
                return operator, version
        return "", ""

    @staticmethod
    def _fallback_extract(candidate: str) -> tuple[str, str]:
        parts = OPERATOR_PATTERN.split(candidate, maxsplit=1)
        if len(parts) >= 3:
            name = parts[0].strip().lower()
            operator = parts[1].strip()
            version = parts[2].strip()
            # ❌ ANTES: return name, f"{operator}{version}" if version else operator
            #  AHORA: Solo devolvemos la versión limpia en el fallback
            return name, version if version else "unspecified"

        return candidate.strip().lower(), "unspecified"
