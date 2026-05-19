"""Tests for the async retry executor in pingram._retry."""
from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest


def _resp(status: int, body: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json=body or {"ok": status < 400})


async def test_returns_immediately_on_2xx():
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(return_value=_resp(200))
    result = await execute_with_retry_async(request_fn, retries=3)
    assert result.status_code == 200
    assert request_fn.await_count == 1


async def test_retries_on_5xx_then_succeeds(mock_sleep):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(side_effect=[_resp(503), _resp(502), _resp(200)])
    result = await execute_with_retry_async(request_fn, retries=3)
    assert result.status_code == 200
    assert request_fn.await_count == 3
    assert mock_sleep.call_count == 2


async def test_returns_final_5xx_after_exhausting_retries(mock_sleep):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(return_value=_resp(503))
    result = await execute_with_retry_async(request_fn, retries=2)
    assert result.status_code == 503
    assert request_fn.await_count == 3


async def test_fails_fast_on_400_no_retry(mock_sleep):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(return_value=_resp(400, {"ok": False, "description": "bad"}))
    result = await execute_with_retry_async(request_fn, retries=3)
    assert result.status_code == 400
    assert request_fn.await_count == 1
    assert mock_sleep.call_count == 0


@pytest.mark.parametrize("status", [401, 403, 404])
async def test_fails_fast_on_other_4xx(mock_sleep, status):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(return_value=_resp(status))
    result = await execute_with_retry_async(request_fn, retries=3)
    assert result.status_code == status
    assert request_fn.await_count == 1
    assert mock_sleep.call_count == 0


async def test_429_honours_retry_after_from_body(mock_sleep):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(side_effect=[
        _resp(429, {"ok": False, "parameters": {"retry_after": 4}}),
        _resp(200),
    ])
    result = await execute_with_retry_async(request_fn, retries=3)
    assert result.status_code == 200
    assert request_fn.await_count == 2
    mock_sleep.assert_called_once_with(4.0)


async def test_429_falls_back_to_backoff_when_no_retry_after(mock_sleep):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(side_effect=[_resp(429, {"ok": False}), _resp(200)])
    result = await execute_with_retry_async(request_fn, retries=3)
    assert result.status_code == 200
    assert mock_sleep.call_count == 1
    (slept,), _ = mock_sleep.call_args
    assert slept > 0


async def test_retries_on_transport_error_then_succeeds(mock_sleep):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(side_effect=[
        httpx.ConnectError("connection refused"),
        _resp(200),
    ])
    result = await execute_with_retry_async(request_fn, retries=3)
    assert result.status_code == 200
    assert request_fn.await_count == 2


async def test_reraises_transport_error_after_exhausting_retries(mock_sleep):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(side_effect=httpx.ConnectError("nope"))
    with pytest.raises(httpx.ConnectError):
        await execute_with_retry_async(request_fn, retries=2)
    assert request_fn.await_count == 3


async def test_retries_zero_means_one_attempt(mock_sleep):
    from pingram._retry import execute_with_retry_async
    request_fn = AsyncMock(return_value=_resp(503))
    result = await execute_with_retry_async(request_fn, retries=0)
    assert result.status_code == 503
    assert request_fn.await_count == 1
    assert mock_sleep.call_count == 0
