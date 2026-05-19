"""Tests for the retry executor in pingram._retry."""
from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest


def _resp(status: int, body: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json=body or {"ok": status < 400})


def test_returns_immediately_on_2xx():
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(return_value=_resp(200))
    result = execute_with_retry(request_fn, retries=3)
    assert result.status_code == 200
    assert request_fn.call_count == 1


def test_retries_on_5xx_then_succeeds(mock_sleep):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(side_effect=[_resp(503), _resp(502), _resp(200)])
    result = execute_with_retry(request_fn, retries=3)
    assert result.status_code == 200
    assert request_fn.call_count == 3
    assert mock_sleep.call_count == 2  # slept between the three attempts


def test_returns_final_5xx_after_exhausting_retries(mock_sleep):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(return_value=_resp(503))
    result = execute_with_retry(request_fn, retries=2)
    assert result.status_code == 503
    assert request_fn.call_count == 3  # 1 initial + 2 retries


def test_fails_fast_on_400_no_retry(mock_sleep):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(return_value=_resp(400, {"ok": False, "description": "bad"}))
    result = execute_with_retry(request_fn, retries=3)
    assert result.status_code == 400
    assert request_fn.call_count == 1
    assert mock_sleep.call_count == 0


@pytest.mark.parametrize("status", [401, 403, 404])
def test_fails_fast_on_other_4xx(mock_sleep, status):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(return_value=_resp(status))
    result = execute_with_retry(request_fn, retries=3)
    assert result.status_code == status
    assert request_fn.call_count == 1
    assert mock_sleep.call_count == 0


def test_429_honours_retry_after_from_body(mock_sleep):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(side_effect=[
        _resp(429, {"ok": False, "parameters": {"retry_after": 4}}),
        _resp(200),
    ])
    result = execute_with_retry(request_fn, retries=3)
    assert result.status_code == 200
    assert request_fn.call_count == 2
    # Must have slept for the retry_after value, not a backoff fallback
    mock_sleep.assert_called_once_with(4.0)


def test_429_falls_back_to_backoff_when_no_retry_after(mock_sleep):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(side_effect=[_resp(429, {"ok": False}), _resp(200)])
    result = execute_with_retry(request_fn, retries=3)
    assert result.status_code == 200
    # Some positive sleep happened
    assert mock_sleep.call_count == 1
    (slept,), _ = mock_sleep.call_args
    assert slept > 0


def test_retries_on_transport_error_then_succeeds(mock_sleep):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(side_effect=[
        httpx.ConnectError("connection refused"),
        _resp(200),
    ])
    result = execute_with_retry(request_fn, retries=3)
    assert result.status_code == 200
    assert request_fn.call_count == 2


def test_reraises_transport_error_after_exhausting_retries(mock_sleep):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(side_effect=httpx.ConnectError("nope"))
    with pytest.raises(httpx.ConnectError):
        execute_with_retry(request_fn, retries=2)
    assert request_fn.call_count == 3


def test_retries_zero_means_one_attempt(mock_sleep):
    from pingram._retry import execute_with_retry
    request_fn = MagicMock(return_value=_resp(503))
    result = execute_with_retry(request_fn, retries=0)
    assert result.status_code == 503
    assert request_fn.call_count == 1
    assert mock_sleep.call_count == 0
