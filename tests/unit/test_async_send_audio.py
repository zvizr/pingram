"""Mocked unit tests for AsyncPingram.send_audio()."""
import httpx

from pingram import AsyncPingram


async def test_send_audio_url_uses_audio_field(
    fake_token, telegram_base, mock_api, ok_response_factory
):
    bot = AsyncPingram(token=fake_token)
    route = mock_api.post(f"{telegram_base}/sendAudio").mock(
        return_value=ok_response_factory()
    )
    await bot.send_audio(chat_id="1", path="https://example.com/x.mp3")
    body = _form_body(route.calls.last.request)
    assert body.get("audio") == "https://example.com/x.mp3"


def _form_body(request: httpx.Request) -> dict[str, str]:
    from urllib.parse import parse_qsl
    return dict(parse_qsl(request.content.decode("utf-8")))
