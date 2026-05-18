from pathlib import Path

from app.parsers.base import DependencyParser
from app.parsers.package_json import PackageJSONParser
from app.parsers.requirements_txt import RequirementsTxtParser


class ParserNotSupportedError(ValueError):
    pass


def get_parser_for_filename(filename: str) -> DependencyParser:
    suffix = Path(filename).name.lower()

    if suffix == "requirements.txt":
        return RequirementsTxtParser()
    if suffix == "package.json":
        return PackageJSONParser()

    raise ParserNotSupportedError(f"No parser available for file: {filename}")
