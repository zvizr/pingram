"""Mocked unit tests for Pingram.send_photo()."""
import httpx

from pingram import Pingram


def test_send_photo_url_posts_field(
    fake_token, telegram_base, mock_api, ok_response_factory
):
    bot = Pingram(token=fake_token)
    route = mock_api.post(f"{telegram_base}/sendPhoto").mock(
        return_value=ok_response_factory()
    )
    # NB: chat_id and path must be str to satisfy 0.3.4's preserved _type validator.
    bot.send_photo(chat_id="1", path="https://example.com/x.jpg", caption="hi")
    body = _form_body(route.calls.last.request)
    assert body.get("photo") == "https://example.com/x.jpg"
    assert body.get("caption") == "hi"
    assert body.get("chat_id") == "1"


def test_send_photo_local_file_uploads_multipart(
    tmp_path, fake_token, telegram_base, mock_api, ok_response_factory
):
    img = tmp_path / "img.jpg"
    img.write_bytes(b"\xff\xd8\xff\xd9")
    bot = Pingram(token=fake_token)
    route = mock_api.post(f"{telegram_base}/sendPhoto").mock(
        return_value=ok_response_factory()
    )
    bot.send_photo(chat_id="1", path=str(img), caption="local")
    req = route.calls.last.request
    assert b"multipart/form-data" in req.headers["content-type"].encode()
    assert b'name="photo"' in req.content


def _form_body(request: httpx.Request) -> dict[str, str]:
    from urllib.parse import parse_qsl
    return dict(parse_qsl(request.content.decode("utf-8")))
