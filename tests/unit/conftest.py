"""Unit-test fixtures.

These tests do NOT touch the real Telegram API. All HTTP traffic is mocked at
the httpx transport layer via respx. Sleep calls in the retry executor are
patched out so the suite runs in milliseconds regardless of backoff config.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
import respx

FAKE_TOKEN = "TEST"
TELEGRAM_BASE = f"https://api.telegram.org/bot{FAKE_TOKEN}"


@pytest.fixture
def fake_token() -> str:
    return FAKE_TOKEN


@pytest.fixture
def telegram_base() -> str:
    return TELEGRAM_BASE


@pytest.fixture
def mock_api() -> respx.MockRouter:
    """Yields a respx router that intercepts every request. Tests configure
    routes per-test."""
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
def ok_response_factory() -> Callable[..., httpx.Response]:
    """Factory for the canonical Telegram 200 OK shape."""
    def make(result: Any = True) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": result})
    return make


@pytest.fixture
def mock_sleep(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patches the retry executor's sleep function so backoff is instant.
    Returns a MagicMock so tests can assert on the durations passed."""
    sleep = MagicMock()
    monkeypatch.setattr("pingram._retry.time.sleep", sleep)
    return sleep
