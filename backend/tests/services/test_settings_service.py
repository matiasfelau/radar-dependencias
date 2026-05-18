from app.services.settings_service import get_scan_interval_seconds


class DummySession:
    def __init__(self, value: str | None):
        self.value = value

    def scalar(self, *_args, **_kwargs):
        return self.value


def test_get_scan_interval_seconds_uses_default_for_invalid_value(monkeypatch) -> None:
    from app.services import settings_service

    monkeypatch.setattr(settings_service, "get_setting_value", lambda *_args, **_kwargs: "abc")
    assert get_scan_interval_seconds(DummySession(None), default=43200) == 43200


def test_get_scan_interval_seconds_uses_positive_value(monkeypatch) -> None:
    from app.services import settings_service

    monkeypatch.setattr(settings_service, "get_setting_value", lambda *_args, **_kwargs: "86400")
    assert get_scan_interval_seconds(DummySession(None), default=43200) == 86400
