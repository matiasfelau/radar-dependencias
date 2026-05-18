from app.services.osv_client import normalize_version_for_osv


def test_normalize_version_for_osv_removes_comparison_prefix() -> None:
    assert normalize_version_for_osv("==1.2.3") == "1.2.3"
    assert normalize_version_for_osv(">=4.5.6") == "4.5.6"


def test_normalize_version_for_osv_rejects_ranges() -> None:
    assert normalize_version_for_osv("^1.2.3 || ^2.0.0") == ""
