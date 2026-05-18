import pytest

from app.parsers.factory import ParserNotSupportedError, get_parser_for_filename
from app.parsers.package_json import PackageJSONParser


def test_package_json_parser_reads_dependencies_and_dev_dependencies() -> None:
    content = b'{"dependencies": {"react": "18.3.1"}, "devDependencies": {"typescript": "5.6.3"}}'

    result = PackageJSONParser().parse(content)

    assert ("react", "18.3.1") in [(item.package_name, item.installed_version) for item in result]
    assert ("typescript", "5.6.3") in [(item.package_name, item.installed_version) for item in result]


def test_package_json_parser_rejects_invalid_payload() -> None:
    with pytest.raises(ValueError):
        PackageJSONParser().parse(b"[]")


def test_factory_chooses_known_parsers() -> None:
    assert get_parser_for_filename("requirements.txt").__class__.__name__ == "RequirementsTxtParser"
    assert get_parser_for_filename("package.json").__class__.__name__ == "PackageJSONParser"

    with pytest.raises(ParserNotSupportedError):
        get_parser_for_filename("pom.xml")
