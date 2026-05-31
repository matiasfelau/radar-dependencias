from app.services.alert_notification_service import _build_update_key, _format_update_message
from app.services.vulnerability_scanner import NewVulnerabilityFinding


def test_build_update_key_is_stable() -> None:
    key = _build_update_key("app", "Production", "react", "18.2.0", "19.0.0")
    assert key == "app/Production/react@18.2.0->19.0.0"


def test_format_update_message_includes_project_and_versions() -> None:
    message = _format_update_message(
        project_name="my-app",
        environment_name="Production",
        package_name="lodash",
        installed_version="4.17.20",
        latest_version="4.17.21",
        dependency_source="npm",
    )

    assert "Actualización disponible" in message
    assert "my-app" in message
    assert "lodash@4.17.20" in message
    assert "4.17.21" in message


def test_new_vulnerability_finding_dataclass() -> None:
    finding = NewVulnerabilityFinding(
        cve_id="CVE-2024-0001",
        package_name="requests",
        affected_version="2.31.0",
        severity="High",
        description="Example vulnerability",
        has_exploit=False,
        exploit_url=None,
    )

    assert finding.cve_id == "CVE-2024-0001"
