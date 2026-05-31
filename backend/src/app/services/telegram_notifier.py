from __future__ import annotations

import html
import logging
import time

import httpx

logger = logging.getLogger(__name__)
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def escape_telegram_html(value: str) -> str:
    return html.escape(value, quote=False)


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    text: str,
    *,
    max_attempts: int = 3,
) -> bool:
    token = bot_token.strip()
    target_chat_id = chat_id.strip()
    if not token or not target_chat_id:
        return False

    url = TELEGRAM_API_URL.format(token=token)
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    delay_seconds = 1.0

    for attempt in range(1, max_attempts + 1):
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text
            logger.warning(
                "Telegram delivery failed (attempt %s/%s, status=%s): %s",
                attempt,
                max_attempts,
                exc.response.status_code,
                error_detail,
            )
            if attempt == max_attempts:
                break
            time.sleep(delay_seconds)
            delay_seconds *= 2
        except httpx.HTTPError as exc:
            logger.warning(
                "Telegram delivery failed (attempt %s/%s): %s",
                attempt,
                max_attempts,
                exc,
            )
            if attempt == max_attempts:
                break
            time.sleep(delay_seconds)
            delay_seconds *= 2

    return False
