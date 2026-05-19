"""Unit-test fixtures.

These tests do NOT touch the real Telegram API. All HTTP traffic is mocked at
the httpx transport layer via respx. Sleep calls in both the sync and async
retry executors are patched out so the suite runs in milliseconds regardless
of backoff config.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

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
    """Patches both the sync retry executor's `time.sleep` and the async
    executor's `asyncio.sleep` so backoff is instant. Returns a MagicMock that
    receives every sleep call (sync or async) so tests can assert on durations.

    The single returned MagicMock collects both kinds of calls. Tests that only
    care about call_count or asserted durations don't need to know which
    executor invoked sleep.

    The async-side patch is guarded with try/except so this fixture works even
    before `_retry.py` has imported `asyncio` (i.e. it's safe to add this
    fixture extension before the async executor lands)."""
    sleep = MagicMock()
    async_sleep = AsyncMock(side_effect=lambda d: sleep(d))
    monkeypatch.setattr("pingram._retry.time.sleep", sleep)
    try:
        monkeypatch.setattr("pingram._retry.asyncio.sleep", async_sleep)
    except (AttributeError, ImportError):
        # asyncio not yet imported in _retry.py; only sync tests run.
        # Once the async executor lands (Task 5), this branch stops firing.
        pass
    return sleep
