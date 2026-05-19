"""Mocked unit tests for AsyncPingram.message()."""
import httpx
import pytest

from pingram import AsyncPingram, TelegramAPIError


async def test_message_posts_to_send_message(
    fake_token, telegram_base, mock_api, ok_response_factory
):
    bot = AsyncPingram(token=fake_token)
    route = mock_api.post(f"{telegram_base}/sendMessage").mock(
        return_value=ok_response_factory({"message_id": 1})
    )
    response = await bot.message(chat_id="123", text="hello")
    assert response.status_code == 200
    assert route.called
    body = _form_body(route.calls.last.request)
    assert body.get("chat_id") == "123"
    assert body.get("text") == "hello"


async def test_message_forwards_extra_kwargs_as_form_data(
    fake_token, telegram_base, mock_api, ok_response_factory
):
    bot = AsyncPingram(token=fake_token)
    route = mock_api.post(f"{telegram_base}/sendMessage").mock(
        return_value=ok_response_factory()
    )
    await bot.message(chat_id="1", text="hi", parse_mode="MarkdownV2", disable_notification=True)
    body = _form_body(route.calls.last.request)
    assert body.get("parse_mode") == "MarkdownV2"
    assert body.get("disable_notification", "").lower() == "true"


async def test_message_strips_underscore_kwargs_from_outbound_payload(
    fake_token, telegram_base, mock_api, ok_response_factory
):
    bot = AsyncPingram(token=fake_token)
    route = mock_api.post(f"{telegram_base}/sendMessage").mock(
        return_value=ok_response_factory()
    )
    await bot.message(chat_id="1", text="hi", _raise=False, _retries=0)
    body = _form_body(route.calls.last.request)
    assert "_raise" not in body
    assert "_retries" not in body


async def test_message_per_call_raise_override(
    fake_token, telegram_base, mock_api
):
    bot = AsyncPingram(token=fake_token, raise_on_error=False)
    mock_api.post(f"{telegram_base}/sendMessage").mock(
        return_value=httpx.Response(400, json={"ok": False, "description": "bad chat"})
    )
    with pytest.raises(TelegramAPIError):
        await bot.message(chat_id="1", text="hi", _raise=True)


def _form_body(request: httpx.Request) -> dict[str, str]:
    from urllib.parse import parse_qsl
    return dict(parse_qsl(request.content.decode("utf-8")))
