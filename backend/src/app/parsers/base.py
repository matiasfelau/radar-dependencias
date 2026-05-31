from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class DependencyEcosystem(StrEnum):
    PYPI = "pypi"
    NPM = "npm"


@dataclass(slots=True, frozen=True)
class ParsedDependency:
    package_name: str
    installed_version: str
    ecosystem: DependencyEcosystem = DependencyEcosystem.PYPI


class DependencyParser(ABC):
    @abstractmethod
    def parse(self, content: bytes) -> list[ParsedDependency]:
        raise NotImplementedError
