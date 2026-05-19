"""Retry executor.

A single function `execute_with_retry` wraps any callable that returns an
`httpx.Response` (or raises `httpx.RequestError`). It applies the policy
documented in the design spec:

  Retryable:     ConnectError, ReadTimeout, WriteTimeout, PoolTimeout, 429, 5xx
  Fail-fast:     400, 401, 403, 404 (return response unchanged on first call)
  429 backoff:   honour `parameters.retry_after` from response body if present
  Other backoff: exponential with jitter, capped

The executor is sleep-injectable for tests via the module-level `time.sleep`
binding (tests patch `pingram._retry.time.sleep`).

`execute_with_retry_async` is the awaitable sibling. Same policy, different
sleep primitive (`asyncio.sleep`), different invocation (`await request_fn()`).
Tests patch `pingram._retry.asyncio.sleep`."""
from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

# Transport-level exceptions that we treat as retryable.
_RETRYABLE_TRANSPORT_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
)

# 4xx statuses for which retrying is pointless.
_FAIL_FAST_STATUSES = frozenset({400, 401, 403, 404})


def execute_with_retry(
    request_fn: Callable[[], httpx.Response],
    *,
    retries: int = 3,
) -> httpx.Response:
    """Sync retry executor. See module docstring for the policy."""
    max_attempts = retries + 1
    last_transport_error: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            response = request_fn()
        except _RETRYABLE_TRANSPORT_EXCEPTIONS as exc:
            last_transport_error = exc
            if attempt + 1 >= max_attempts:
                raise
            time.sleep(_backoff_seconds(attempt))
            continue

        if response.status_code in _FAIL_FAST_STATUSES:
            return response

        if response.status_code == 429:
            if attempt + 1 >= max_attempts:
                return response
            time.sleep(_retry_after_seconds(response) or _backoff_seconds(attempt))
            continue

        if 500 <= response.status_code < 600:
            if attempt + 1 >= max_attempts:
                return response
            time.sleep(_backoff_seconds(attempt))
            continue

        return response

    assert last_transport_error is not None
    raise last_transport_error


async def execute_with_retry_async(
    request_fn: Callable[[], Awaitable[httpx.Response]],
    *,
    retries: int = 3,
) -> httpx.Response:
    """Async retry executor. Mirror of `execute_with_retry` with `await
    request_fn()` and `await asyncio.sleep(...)`."""
    max_attempts = retries + 1
    last_transport_error: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            response = await request_fn()
        except _RETRYABLE_TRANSPORT_EXCEPTIONS as exc:
            last_transport_error = exc
            if attempt + 1 >= max_attempts:
                raise
            await asyncio.sleep(_backoff_seconds(attempt))
            continue

        if response.status_code in _FAIL_FAST_STATUSES:
            return response

        if response.status_code == 429:
            if attempt + 1 >= max_attempts:
                return response
            await asyncio.sleep(_retry_after_seconds(response) or _backoff_seconds(attempt))
            continue

        if 500 <= response.status_code < 600:
            if attempt + 1 >= max_attempts:
                return response
            await asyncio.sleep(_backoff_seconds(attempt))
            continue

        return response

    assert last_transport_error is not None
    raise last_transport_error


def _backoff_seconds(attempt: int) -> float:
    """Exponential backoff with full jitter. attempt is 0-indexed."""
    base = min(2 ** attempt, 4)
    return random.uniform(0, base)


def _retry_after_seconds(response: httpx.Response) -> float | None:
    body = _safe_json(response)
    if isinstance(body, dict):
        params = body.get("parameters")
        if isinstance(params, dict):
            ra = params.get("retry_after")
            if isinstance(ra, (int, float)):
                return float(ra)
    return None


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return None
