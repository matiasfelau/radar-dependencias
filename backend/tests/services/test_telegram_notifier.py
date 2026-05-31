from app.services.telegram_notifier import escape_telegram_html, send_telegram_message


class DummyResponse:
    def __init__(self) -> None:
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None


class DummyClient:
    def __init__(self, *_args, **_kwargs) -> None:
        self.last_payload: dict[str, object] | None = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def post(self, _url: str, json: dict[str, object]):
        self.last_payload = json
        return DummyResponse()


def test_escape_telegram_html_escapes_special_characters() -> None:
    assert escape_telegram_html("a & b <script>") == "a &amp; b &lt;script&gt;"


def test_send_telegram_message_posts_html_payload(monkeypatch) -> None:
    dummy_client = DummyClient()

    class ClientFactory:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            return dummy_client

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr("app.services.telegram_notifier.httpx.Client", ClientFactory)

    assert send_telegram_message("token", "123", "hello") is True
    assert dummy_client.last_payload == {
        "chat_id": "123",
        "text": "hello",
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }


def test_send_telegram_message_returns_false_without_credentials() -> None:
    assert send_telegram_message("", "123", "hello") is False
    assert send_telegram_message("token", "", "hello") is False
