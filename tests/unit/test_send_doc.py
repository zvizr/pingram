"""Mocked unit tests for Pingram.send_doc()."""
import httpx

from pingram import Pingram


def test_send_doc_url_uses_document_field(
    fake_token, telegram_base, mock_api, ok_response_factory
):
    bot = Pingram(token=fake_token)
    route = mock_api.post(f"{telegram_base}/sendDocument").mock(
        return_value=ok_response_factory()
    )
    bot.send_doc(chat_id="1", path="https://example.com/x.pdf", caption="report")
    body = _form_body(route.calls.last.request)
    assert body.get("document") == "https://example.com/x.pdf"
    assert body.get("caption") == "report"


def test_send_doc_local_file_uploads_multipart(
    tmp_path, fake_token, telegram_base, mock_api, ok_response_factory
):
    f = tmp_path / "report.pdf"
    f.write_bytes(b"%PDF-1.4\n")
    bot = Pingram(token=fake_token)
    route = mock_api.post(f"{telegram_base}/sendDocument").mock(
        return_value=ok_response_factory()
    )
    bot.send_doc(chat_id="1", path=str(f))
    req = route.calls.last.request
    assert b'name="document"' in req.content


def _form_body(request: httpx.Request) -> dict[str, str]:
    from urllib.parse import parse_qsl
    return dict(parse_qsl(request.content.decode("utf-8")))
