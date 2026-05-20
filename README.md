[![PyPI Downloads](https://static.pepy.tech/personalized-badge/pingram?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/pingram)
[![Python](https://img.shields.io/pypi/pyversions/pingram)](https://pypi.org/project/pingram/)
[![PyPI version](https://img.shields.io/pypi/v/pingram.svg)](https://pypi.org/project/pingram/)
[![CI](https://github.com/zvizr/pingram/actions/workflows/ci.yml/badge.svg)](https://github.com/zvizr/pingram/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/zvizr/pingram)](LICENSE)

# Pingram

Send Telegram messages with one line of Python. No webhooks. No bloat. Just pings.

Pingram is an ultra-lightweight Python wrapper for sending outbound Telegram messages via your bot. It's designed as a cost-free alternative to email and SMS, focused on one-way "ping"-style messaging — ideal for alerts, reports, logs, and automated notifications.

> Looking for a minimal alternative to `python-telegram-bot`? Pingram avoids the event loop, handlers, and 7.8MB install size, focusing solely on *outbound pings* with just one method per use case.

---

## Lightweight by Design

Pingram prioritizes size, speed, and clarity. Designed to be imported and deployed instantly.

| Package                  | Size        |
|--------------------------|-------------|
| Pingram (core)           | ~20 KB      |
| Pingram + AsyncPingram   | ~21 KB      |
| Pingram + httpx          | ~800 KB     |
| python-telegram-bot      | ~7.8 MB     |


Result:

- Pingram is **over 9× smaller** than PTB even with `httpx` included.
- Pingram core is **~390× smaller** than PTB alone.
- That's a ~90% reduction with dependencies, and ~99.7% without.


Perfect for:

- Minimal Docker containers
- Constrained environments
- Clean, single-purpose automation

## Features

- Send messages, photos, documents, audio, and video
- Direct method calls: `bot.message()`, `bot.send_photo()`, etc.
- **Sync and async clients** — `Pingram` (sync) + `AsyncPingram` (async) with identical APIs
- Minimalistic architecture, no listeners or webhooks
- Built on `httpx` (sync + async)
- Retries with backoff on transient failures (429, 5xx, network errors)
- Typed exception hierarchy you can opt into
- No webhook setup required

## Who is it for?

- Developers who want zero-setup Telegram alerts
- Sysadmins replacing email/SMS for cron/CI jobs
- Raspberry Pi or IoT projects needing compact tooling
- Traders, scrapers, and bots that need lightweight push

## Installation

```bash
pip install pingram
```

Requires Python 3.9 or newer.

## Quickstart

```python
from pingram import Pingram

bot = Pingram(token="<BOT_TOKEN>")
bot.me()
```

> *A simple method for testing your bot's authentication token. Requires no parameters. Returns basic information about the bot in form of a User object.* https://core.telegram.org/bots/api#getme

Since every high-level api function returns a `httpx.Response` object, you can append the end of a function call using `.text` to show the raw HTTP response instead of the status code.

```python
bot.message(chat_id=123456789, text="Hello Friend").text
```

This call returns a success or error message from the Telegram API.

## Async usage

For asyncio applications, FastAPI handlers, Jupyter notebooks, or anywhere you want to fire multiple pings concurrently, use `AsyncPingram`. It mirrors the sync API exactly — same methods, same kwargs, same typed errors.

```python
import asyncio
from pingram import AsyncPingram

async def main():
    async with AsyncPingram(token="<BOT_TOKEN>") as bot:
        await asyncio.gather(
            bot.message(chat_id=123, text="step 1 done"),
            bot.message(chat_id=123, text="step 2 done"),
            bot.send_photo(chat_id=123, path="chart.png"),
        )

asyncio.run(main())
```

Three supported lifecycle shapes:

```python
# 1. async with (recommended — guarantees client cleanup)
async with AsyncPingram(token="...") as bot:
    await bot.message(chat_id=123, text="hi")

# 2. manual aclose (parity with how Pingram is used)
bot = AsyncPingram(token="...")
try:
    await bot.message(chat_id=123, text="hi")
finally:
    await bot.aclose()

# 3. fire-and-forget (allowed but emits a resource warning at GC time)
bot = AsyncPingram(token="...")
await bot.message(chat_id=123, text="hi")
```

Retries, typed errors (`PingramError`, `TelegramAPIError`, `RateLimitError`, `TransportError`), and per-call `_raise` / `_retries` overrides all work identically to the sync `Pingram`. See the **Error handling** and **Retry policy** sections below.

## Media Examples

> All media-sending methods accept both local file paths and direct URLs.
> Ensure URLs are direct links (i.e. ending in `.jpg`, `.mp4`, `.pdf`) and serve correct `Content-Type` headers.

### Send Photo

```python
bot.send_photo(
    chat_id=123456789,
    path="https://example.com/image.jpg",
    caption="Test Photo"
)
```

From a local file:

```python
bot.send_photo(
    chat_id=123456789,
    path="photo.jpg",
    caption="Local Image"
)
```

### Send Document

```python
bot.send_doc(
    chat_id=123456789,
    path="https://example.com/file.pdf",
    caption="Monthly Report"
)
```

From a local file:

```python
bot.send_doc(
    chat_id=123456789,
    path="report.pdf",
    caption="Monthly Report"
)
```

### Send Audio

```python
bot.send_audio(
    chat_id=123456789,
    path="https://www.myinstants.com//media/sounds/hello-friend-mr-robot.mp3",
    caption="Greetings."
)
```

From a local file:

```python
bot.send_audio(
    chat_id=123456789,
    path="audio.mp3",
    caption="Shower Thoughts"
)
```

### Send Video

```python
bot.send_video(
    chat_id=123456789,
    path="https://yourdomain.com/video.mp4",  # must be direct link to .mp4
    caption="Security Footage"
)
```

From a local file:

```python
bot.send_video(
    chat_id=123456789,
    path="stranger.mp4",
    caption="Security Footage"
)
```

## Additional Request Data

Including additional data such as a caption, description or any other key, value types supported by the Telegram API can be passed through any API call simply by including it in the params of the function.

```python
bot.send_video(
    chat_id=123456789,
    path="hamsters.mp4",
    caption="Playful Hamsters",
    has_spoiler=True
)
```

> The `has_spoiler` parameter is a native Telegram option. It must be passed as a bool.

## Error handling

By default, pingram preserves the 0.3.x contract: methods return the final `httpx.Response` even if it carries a non-2xx status, and transport errors propagate as their underlying `httpx` exceptions.

Opt into typed exceptions with `raise_on_error=True`:

```python
from pingram import Pingram, PingramError, RateLimitError, TelegramAPIError, TransportError

bot = Pingram(token="<BOT_TOKEN>", raise_on_error=True, retries=5)

try:
    bot.message(chat_id=123, text="hello")
except RateLimitError as exc:
    # exc.retry_after carries Telegram's suggested delay if provided
    ...
except TelegramAPIError as exc:
    # non-2xx response that retries couldn't fix
    print(exc.status_code, exc.description)
except TransportError as exc:
    # network/transport failure after retries exhausted
    ...
except PingramError:
    # catch-all base if you prefer
    ...
```

You can also override per call:

```python
bot.message(chat_id=123, text="hello", _raise=True, _retries=0)
```

`_raise` and `_retries` kwargs are stripped before the payload is forwarded to Telegram.

## MarkdownV2 escaping

Telegram's MarkdownV2 parse mode needs backslash-escaping for a long list of characters. Pingram ships three small helpers so you don't have to remember which is which:

```python
from pingram import (
    escape_markdown_v2,
    escape_markdown_v2_code,
    escape_markdown_v2_link_url,
)

# Plain text body
bot.message(
    chat_id=123,
    text=f"⚠️ *{escape_markdown_v2(hostname)}* is down",
    parse_mode="MarkdownV2",
)

# Inside an inline code span (only backtick and backslash need escaping)
bot.message(
    chat_id=123,
    text=f"Run `{escape_markdown_v2_code(command)}` to retry",
    parse_mode="MarkdownV2",
)

# Inside a link URL (only `)` and backslash need escaping)
bot.message(
    chat_id=123,
    text=f"[details]({escape_markdown_v2_link_url(url)})",
    parse_mode="MarkdownV2",
)
```

The helpers are pure functions — no `await`, no client needed.

## Retry policy

| Condition | Behaviour |
|---|---|
| 2xx / 3xx | Return immediately |
| 400, 401, 403, 404 | Fail-fast — no retry |
| 429 | Retry; honour `parameters.retry_after` if present, else exponential backoff |
| 5xx | Retry with exponential backoff |
| Connection error / timeout | Retry with exponential backoff |

Set `retries=0` for pre-0.4.0 behaviour (single attempt, no retries).

## Tests

Pingram ships a two-tier test suite:

- **Unit tests** (`tests/unit/`) — fast, deterministic, mocked at the httpx transport layer with [`respx`](https://github.com/lundberg/respx). These run on every PR via GitHub Actions across Python 3.9–3.13.
- **Integration tests** (`tests/integration/`) — opt-in, real-API tests that send actual messages. Useful for edge-case detection (rate limits, content-type mismatches). Require `BOT_TOKEN` + `CHAT_ID` env vars and are run from `main` only.

To run them locally:

```bash
# Unit tests (no creds required)
pytest

# Integration tests (real-API, .env with BOT_TOKEN + CHAT_ID)
pytest tests/integration -m integration
```

## Roadmap

- [x] Retry and error handling
- [x] Package tests and CI integration
- [x] Async mode (`AsyncPingram`)
- [ ] Message templating engine
- [ ] Std input/message collectors
- [ ] Webhook-to-Telegram bridge

---

Maintained — [issues and PRs](https://github.com/zvizr/pingram/issues) welcome.
