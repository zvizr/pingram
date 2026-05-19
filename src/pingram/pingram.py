# SPDX-FileCopyrightText: 2026-present zvizr <zvizr@proton.me>
#
# SPDX-License-Identifier: MIT
"""Pingram — sync Telegram bot wrapper for outbound pings."""
from __future__ import annotations

from typing import Any, Union

import httpx

from pingram._errors import (
    RateLimitError,
    TelegramAPIError,
    TransportError,
)
from pingram._retry import execute_with_retry

__all__ = ["Pingram"]


class Pingram:
    """Send outbound Telegram messages via a bot token.

    Parameters
    ----------
    token:
        The bot token from @BotFather.
    retries:
        Number of retries on transient failure (transport errors, 429, 5xx).
        Default 3. Use 0 to disable retries (0.3.4 behaviour).
    raise_on_error:
        When True, non-2xx responses raise `TelegramAPIError` (`RateLimitError`
        for 429) and transport errors raise `TransportError`. When False
        (default), the original 0.3.4 contract is preserved: methods return
        the final `httpx.Response` even when it is non-2xx, and underlying
        httpx exceptions propagate naturally.
    timeout:
        Per-request timeout in seconds. Default 10.0 (the hardcoded 0.3.4 value).

    Per-call overrides
    ------------------
    Any public method accepts `_raise=True/False` and `_retries=N` kwargs that
    override the instance defaults for that single call. These kwargs are
    stripped before forwarding to the Telegram API."""

    def __init__(
        self,
        token: str,
        *,
        retries: int = 3,
        raise_on_error: bool = False,
        timeout: float = 10.0,
    ) -> None:
        self.token = token
        self._retries = retries
        self._raise_on_error = raise_on_error
        self._timeout = timeout
        self.client = httpx.Client()
        self.endpoints = {
            "me": f"https://api.telegram.org/bot{token}/getMe",
            "msg": f"https://api.telegram.org/bot{token}/sendMessage",
            "photo": f"https://api.telegram.org/bot{token}/sendPhoto",
            "doc": f"https://api.telegram.org/bot{token}/sendDocument",
            "audio": f"https://api.telegram.org/bot{token}/sendAudio",
            "video": f"https://api.telegram.org/bot{token}/sendVideo",
        }

    # ----- public API ----------------------------------------------------

    def me(self, **kwargs: Any) -> httpx.Response:
        raise_on_error, retries = self._pop_meta(kwargs)
        return self._execute(
            lambda: self._raw_get("me"),
            raise_on_error=raise_on_error,
            retries=retries,
        )

    def message(self, chat_id: Union[str, int], text: str, **kwargs: Any) -> httpx.Response:
        raise_on_error, retries = self._pop_meta(kwargs)
        self._type({chat_id: str})
        payload = {"chat_id": str(chat_id), "text": text, **kwargs}
        return self._execute(
            lambda: self._raw_post("msg", payload),
            raise_on_error=raise_on_error,
            retries=retries,
        )

    def send_photo(
        self,
        chat_id: Union[str, int],
        path: str,
        caption: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return self._send_media("photo", chat_id, path, "photo", caption, kwargs)

    def send_doc(
        self,
        chat_id: Union[str, int],
        path: str,
        caption: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return self._send_media("doc", chat_id, path, "document", caption, kwargs)

    def send_audio(
        self,
        chat_id: Union[str, int],
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        return self._send_media("audio", chat_id, path, "audio", None, kwargs)

    def send_video(
        self,
        chat_id: Union[str, int],
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        return self._send_media("video", chat_id, path, "video", None, kwargs)

    # ----- internals -----------------------------------------------------

    def _pop_meta(self, kwargs: dict[str, Any]) -> tuple[bool, int]:
        raise_on_error = kwargs.pop("_raise", self._raise_on_error)
        retries = kwargs.pop("_retries", self._retries)
        return raise_on_error, retries

    def _send_media(
        self,
        endpoint_key: str,
        chat_id: Union[str, int],
        path: str,
        field: str,
        caption: str | None,
        kwargs: dict[str, Any],
    ) -> httpx.Response:
        raise_on_error, retries = self._pop_meta(kwargs)
        self._type({chat_id: str, path: str})
        data: dict[str, Any] = {"chat_id": str(chat_id), **kwargs}
        if caption is not None:
            data["caption"] = caption
        if path.startswith("http"):
            data[field] = path
            return self._execute(
                lambda: self._raw_post(endpoint_key, data),
                raise_on_error=raise_on_error,
                retries=retries,
            )

        # Local file: open once per attempt so retries can re-read.
        def request_fn() -> httpx.Response:
            with open(path, "rb") as fh:
                return self._raw_post(endpoint_key, data, files={field: fh})

        return self._execute(
            request_fn, raise_on_error=raise_on_error, retries=retries
        )

    def _execute(
        self,
        request_fn,
        *,
        raise_on_error: bool,
        retries: int,
    ) -> httpx.Response:
        try:
            response = execute_with_retry(request_fn, retries=retries)
        except httpx.RequestError as exc:
            if raise_on_error:
                raise TransportError(str(exc)) from exc
            raise
        if raise_on_error and response.status_code >= 400:
            raise self._classify_response_error(response)
        return response

    @staticmethod
    def _classify_response_error(response: httpx.Response) -> TelegramAPIError:
        if response.status_code == 429:
            return RateLimitError(response=response)
        return TelegramAPIError(response=response)

    def _raw_get(self, key: str, data: dict[str, Any] | None = None) -> httpx.Response:
        return self.client.get(url=self.endpoints[key], params=data, timeout=self._timeout)

    def _raw_post(
        self,
        key: str,
        data: dict[str, Any],
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        filtered = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))}
        return self.client.post(
            url=self.endpoints[key], data=filtered, files=files, timeout=self._timeout
        )

    @staticmethod
    def _type(type_map: dict[Any, type]) -> bool:
        """Preserved from 0.3.4. Validates value/type pairs; raises TypeError
        on mismatch. The argument shape (value as key) is awkward and
        intentionally unchanged to keep callers working."""
        for value, expected_type in type_map.items():
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"Expected {value!r} to be of type {expected_type}, got {type(value)}"
                )
        return True
