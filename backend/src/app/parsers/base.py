from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ParsedDependency:
    package_name: str
    installed_version: str


class DependencyParser(ABC):
    @abstractmethod
    def parse(self, content: bytes) -> list[ParsedDependency]:
        raise NotImplementedError
