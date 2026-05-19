# SPDX-FileCopyrightText: 2026-present zvizr <zvizr@proton.me>
#
# SPDX-License-Identifier: MIT
"""AsyncPingram — async sibling of Pingram.

Mirrors the sync API surface with `await` semantics. Shares the typed
exception hierarchy from `pingram._errors` and the retry policy from
`pingram._retry.execute_with_retry_async`."""
from __future__ import annotations

from typing import Any

import httpx

from pingram._errors import (
    RateLimitError,
    TelegramAPIError,
    TransportError,
)
from pingram._retry import execute_with_retry_async

__all__ = ["AsyncPingram"]


class AsyncPingram:
    """Async Telegram bot client. Mirror of `Pingram` with `await` on every
    public method.

    Parameters mirror `Pingram` exactly: `token`, `retries=3`,
    `raise_on_error=False`, `timeout=10.0`. Per-call overrides via `_raise`
    and `_retries` kwargs work identically.

    Lifecycle: prefer `async with AsyncPingram(...) as bot: ...` to guarantee
    the underlying `httpx.AsyncClient` is closed. Manual `await bot.aclose()`
    works too."""

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
        self.client = httpx.AsyncClient()
        self.endpoints = {
            "me": f"https://api.telegram.org/bot{token}/getMe",
            "msg": f"https://api.telegram.org/bot{token}/sendMessage",
            "photo": f"https://api.telegram.org/bot{token}/sendPhoto",
            "doc": f"https://api.telegram.org/bot{token}/sendDocument",
            "audio": f"https://api.telegram.org/bot{token}/sendAudio",
            "video": f"https://api.telegram.org/bot{token}/sendVideo",
        }

    # ----- lifecycle ------------------------------------------------------

    async def aclose(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncPingram":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()

    # ----- public API -----------------------------------------------------

    async def me(self, **kwargs: Any) -> httpx.Response:
        raise_on_error, retries = self._pop_meta(kwargs)
        return await self._execute_async(
            self._make_get("me"),
            raise_on_error=raise_on_error,
            retries=retries,
        )

    async def message(
        self, chat_id: str | int, text: str, **kwargs: Any
    ) -> httpx.Response:
        raise_on_error, retries = self._pop_meta(kwargs)
        self._type({chat_id: str})
        payload = {"chat_id": str(chat_id), "text": text, **kwargs}
        return await self._execute_async(
            self._make_post("msg", payload),
            raise_on_error=raise_on_error,
            retries=retries,
        )

    async def send_photo(
        self,
        chat_id: str | int,
        path: str,
        caption: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return await self._send_media("photo", chat_id, path, "photo", caption, kwargs)

    async def send_doc(
        self,
        chat_id: str | int,
        path: str,
        caption: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return await self._send_media("doc", chat_id, path, "document", caption, kwargs)

    async def send_audio(
        self,
        chat_id: str | int,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        return await self._send_media("audio", chat_id, path, "audio", None, kwargs)

    async def send_video(
        self,
        chat_id: str | int,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        return await self._send_media("video", chat_id, path, "video", None, kwargs)

    # ----- internals ------------------------------------------------------

    def _pop_meta(self, kwargs: dict[str, Any]) -> tuple[bool, int]:
        raise_on_error = kwargs.pop("_raise", self._raise_on_error)
        retries = kwargs.pop("_retries", self._retries)
        return raise_on_error, retries

    async def _send_media(
        self,
        endpoint_key: str,
        chat_id: str | int,
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
            return await self._execute_async(
                self._make_post(endpoint_key, data),
                raise_on_error=raise_on_error,
                retries=retries,
            )

        # Local file: re-open per attempt so retries can re-read.
        async def request_fn() -> httpx.Response:
            with open(path, "rb") as fh:
                return await self._raw_post_async(
                    endpoint_key, data, files={field: fh}
                )

        return await self._execute_async(
            request_fn, raise_on_error=raise_on_error, retries=retries
        )

    def _make_get(self, key: str):
        async def request_fn() -> httpx.Response:
            return await self._raw_get_async(key)
        return request_fn

    def _make_post(self, key: str, payload: dict[str, Any]):
        async def request_fn() -> httpx.Response:
            return await self._raw_post_async(key, payload)
        return request_fn

    async def _execute_async(
        self,
        request_fn,
        *,
        raise_on_error: bool,
        retries: int,
    ) -> httpx.Response:
        try:
            response = await execute_with_retry_async(request_fn, retries=retries)
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

    async def _raw_get_async(
        self, key: str, data: dict[str, Any] | None = None
    ) -> httpx.Response:
        return await self.client.get(
            url=self.endpoints[key], params=data, timeout=self._timeout
        )

    async def _raw_post_async(
        self,
        key: str,
        data: dict[str, Any],
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        filtered = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))}
        return await self.client.post(
            url=self.endpoints[key], data=filtered, files=files, timeout=self._timeout
        )

    @staticmethod
    def _type(type_map: dict[Any, type]) -> bool:
        """Same odd-shape validator as sync Pingram. Preserved for parity."""
        for value, expected_type in type_map.items():
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"Expected {value!r} to be of type {expected_type}, got {type(value)}"
                )
        return True
