from app.parsers.requirements_txt import RequirementsTxtParser


def test_requirements_parser_handles_basic_and_comments() -> None:
    content = b"""
    # comment
    fastapi==0.115.0
    uvicorn>=0.30.0
    """

    result = RequirementsTxtParser().parse(content)

    assert [(item.package_name, item.installed_version) for item in result] == [
        ("fastapi", "==0.115.0"),
        ("uvicorn", ">=0.30.0"),
    ]


def test_requirements_parser_handles_extras_and_unspecified() -> None:
    content = b"""
    requests[socks]==2.32.3
    pydantic
    -r base.txt
    """

    result = RequirementsTxtParser().parse(content)

    assert ("pydantic", "unspecified") in [(item.package_name, item.installed_version) for item in result]
    assert ("requests[socks]", "==2.32.3") in [
        (item.package_name, item.installed_version) for item in result
    ]
