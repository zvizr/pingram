"""Tests for the typed exception hierarchy."""
import httpx
import pytest


def test_pingram_error_is_exception():
    from pingram import PingramError
    assert issubclass(PingramError, Exception)


def test_transport_error_inherits_pingram_error():
    from pingram import PingramError, TransportError
    assert issubclass(TransportError, PingramError)


def test_telegram_api_error_inherits_pingram_error():
    from pingram import PingramError, TelegramAPIError
    assert issubclass(TelegramAPIError, PingramError)


def test_rate_limit_error_inherits_telegram_api_error():
    from pingram import RateLimitError, TelegramAPIError
    assert issubclass(RateLimitError, TelegramAPIError)


def test_telegram_api_error_carries_status_and_description():
    from pingram import TelegramAPIError
    resp = httpx.Response(400, json={"ok": False, "description": "bad"})
    err = TelegramAPIError(response=resp)
    assert err.status_code == 400
    assert err.description == "bad"
    assert err.response is resp


def test_telegram_api_error_description_is_none_when_absent():
    from pingram import TelegramAPIError
    resp = httpx.Response(500, json={"ok": False})
    err = TelegramAPIError(response=resp)
    assert err.description is None


def test_rate_limit_error_carries_retry_after():
    from pingram import RateLimitError
    resp = httpx.Response(
        429,
        json={"ok": False, "description": "Too Many Requests",
              "parameters": {"retry_after": 7}},
    )
    err = RateLimitError(response=resp)
    assert err.retry_after == 7.0
    assert err.status_code == 429


def test_rate_limit_error_retry_after_is_none_when_absent():
    from pingram import RateLimitError
    resp = httpx.Response(429, json={"ok": False})
    err = RateLimitError(response=resp)
    assert err.retry_after is None
