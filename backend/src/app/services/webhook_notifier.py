from __future__ import annotations

import logging
import time
from collections.abc import Mapping

import httpx

logger = logging.getLogger(__name__)


def post_webhook_with_retry(
    webhook_url: str,
    payload: Mapping[str, object],
    max_attempts: int = 3,
) -> bool:
    delay_seconds = 1.0

    for attempt in range(1, max_attempts + 1):
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(webhook_url, json=dict(payload))
                response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.warning(
                "Webhook delivery failed (attempt %s/%s) to %s: %s",
                attempt,
                max_attempts,
                webhook_url,
                exc,
            )
            if attempt == max_attempts:
                break
            time.sleep(delay_seconds)
            delay_seconds *= 2

    return False
