"""Typed exception hierarchy for pingram.

Public types are re-exported from `pingram` (the package). The underscore
prefix on this module marks it as internal — only the exception classes
themselves are part of the public API."""
from __future__ import annotations

from typing import Any

import httpx


class PingramError(Exception):
    """Base for all pingram-raised errors. Catch this to handle anything
    pingram might raise without depending on httpx exception types."""


class TransportError(PingramError):
    """Raised when the underlying HTTP transport fails (connection refused,
    timeout, etc.) and `raise_on_error=True` is set. Without that flag, the
    original httpx exception propagates unchanged (the 0.3.4 contract)."""


class TelegramAPIError(PingramError):
    """Raised when the Telegram API returns a non-2xx response and
    `raise_on_error=True` is set."""

    def __init__(self, *, response: httpx.Response) -> None:
        self.response = response
        self.status_code = response.status_code
        self.description: str | None = _extract_description(response)
        super().__init__(self._format())

    def _format(self) -> str:
        if self.description:
            return f"Telegram API error {self.status_code}: {self.description}"
        return f"Telegram API error {self.status_code}"


class RateLimitError(TelegramAPIError):
    """Raised on HTTP 429 when `raise_on_error=True`. Exposes
    `retry_after` (seconds) from the response body's `parameters.retry_after`
    if Telegram included it; otherwise `None`."""

    def __init__(self, *, response: httpx.Response) -> None:
        super().__init__(response=response)
        self.retry_after: float | None = _extract_retry_after(response)


def _extract_description(response: httpx.Response) -> str | None:
    body = _safe_json(response)
    if isinstance(body, dict):
        desc = body.get("description")
        if isinstance(desc, str):
            return desc
    return None


def _extract_retry_after(response: httpx.Response) -> float | None:
    body = _safe_json(response)
    if isinstance(body, dict):
        params = body.get("parameters")
        if isinstance(params, dict):
            ra = params.get("retry_after")
            if isinstance(ra, (int, float)):
                return float(ra)
    return None


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
