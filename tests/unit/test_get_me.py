"""Mocked unit tests for Pingram.me()."""
import httpx
import pytest

from pingram import Pingram, RateLimitError, TelegramAPIError, TransportError


def test_me_returns_response_on_success(fake_token, telegram_base, mock_api, ok_response_factory):
    bot = Pingram(token=fake_token)
    mock_api.get(f"{telegram_base}/getMe").mock(
        return_value=ok_response_factory({"id": 1, "is_bot": True, "username": "x"})
    )
    response = bot.me()
    assert response.status_code == 200
    assert response.json()["result"]["username"] == "x"


def test_me_retries_on_503_then_succeeds(
    fake_token, telegram_base, mock_api, ok_response_factory, mock_sleep
):
    bot = Pingram(token=fake_token, retries=2)
    route = mock_api.get(f"{telegram_base}/getMe").mock(
        side_effect=[
            httpx.Response(503, json={"ok": False}),
            ok_response_factory({"id": 1}),
        ]
    )
    response = bot.me()
    assert response.status_code == 200
    assert route.call_count == 2


def test_me_does_not_retry_when_retries_zero(
    fake_token, telegram_base, mock_api, mock_sleep
):
    bot = Pingram(token=fake_token, retries=0)
    route = mock_api.get(f"{telegram_base}/getMe").mock(
        return_value=httpx.Response(503, json={"ok": False})
    )
    response = bot.me()
    assert response.status_code == 503
    assert route.call_count == 1
    assert mock_sleep.call_count == 0


def test_me_raises_telegram_api_error_when_raise_on_error_true(
    fake_token, telegram_base, mock_api
):
    bot = Pingram(token=fake_token, raise_on_error=True)
    mock_api.get(f"{telegram_base}/getMe").mock(
        return_value=httpx.Response(401, json={"ok": False, "description": "Unauthorized"})
    )
    with pytest.raises(TelegramAPIError) as exc_info:
        bot.me()
    assert exc_info.value.status_code == 401
    assert exc_info.value.description == "Unauthorized"


def test_me_raises_rate_limit_error_on_429(
    fake_token, telegram_base, mock_api, mock_sleep
):
    bot = Pingram(token=fake_token, raise_on_error=True, retries=0)
    mock_api.get(f"{telegram_base}/getMe").mock(
        return_value=httpx.Response(
            429,
            json={"ok": False, "description": "Too Many Requests",
                  "parameters": {"retry_after": 3}},
        )
    )
    with pytest.raises(RateLimitError) as exc_info:
        bot.me()
    assert exc_info.value.retry_after == 3.0


def test_me_raises_transport_error_when_raise_on_error_true(
    fake_token, telegram_base, mock_api, mock_sleep
):
    bot = Pingram(token=fake_token, raise_on_error=True, retries=1)
    mock_api.get(f"{telegram_base}/getMe").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(TransportError):
        bot.me()


def test_me_propagates_naked_httpx_error_by_default(
    fake_token, telegram_base, mock_api, mock_sleep
):
    bot = Pingram(token=fake_token, retries=1)  # default raise_on_error=False
    mock_api.get(f"{telegram_base}/getMe").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(httpx.ConnectError):
        bot.me()


def test_me_per_call_raise_override(
    fake_token, telegram_base, mock_api
):
    bot = Pingram(token=fake_token, raise_on_error=False)
    mock_api.get(f"{telegram_base}/getMe").mock(
        return_value=httpx.Response(401, json={"ok": False})
    )
    with pytest.raises(TelegramAPIError):
        bot.me(_raise=True)
