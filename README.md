
# Pingram

Pingram is an ultra-lightweight Python wrapper for sending outbound Telegram messages via your bot. It’s designed as a cost-free alternative to email and SMS, focused on one-way “ping”-style messaging — ideal for alerts, reports, logs, and automated notifications.

## Features

- Send messages, photos, documents, audio, and video
- Direct method calls: `bot.message`, `bot.send_photo`, etc.
- Minimalistic architecture (single file, no external listeners)
- Built on `httpx` (sync client)
- No webhook setup or event loop required

## Installation

```bash
pip install pingram
```

## Quickstart

```python
from pingram import Pingram

bot = Pingram(token="<BOT_TOKEN>")
bot.message(chat_id=123456789, text="Hello Friend")
```

Since every high-level api function returns a http.Response object, you can append the end of a function call using ```.text``` to show the raw HTTP response instead of the status code.

```python
bot.message(chat_id=123456789, text="Hello Friend").text
```

This particular call will return a success of failure message from the Telegram API.


## Media Examples

Send Photo

```python
bot.send_photo(
    chat_id=123456789,
    path="https://example.com/image.jpg",
    caption="Test Photo"
)
```

### From local file:

```python
bot.send_photo(
    chat_id=123456789,
    path="photo.jpg",
    caption="Local Image"
)
```


## Send Document

```python
bot.send_doc(
    chat_id=123456789,
    path="https://example.com/file.pdf",
    caption="Monthly Report"
)
```

## Send Audio

```python
bot.send_audio(
    chat_id=123456789,
    path="audio.mp3",
    caption="Shower Thoughts"
)
```

## Send Video

```python
bot.send_video(
    chat_id=123456789,
    path="https://example.com/clip.mp4",
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

We included an additional "has_spoiler" parameter that requires interpolation of a bool data type.


## Benefits

- Eliminates SMTP and SMS costs
- No server or inbound infra required
- Uses only a Telegram bot token
- Lightweight and auditable codebase
- Ideal for scripts, automation, and event pings
- Seamless integration with CLI tools, logs, or system alerts

## Planned features

- Retry and error handling
- Async mode (httpx.AsyncClient)
- Message templating engine
- Std input/message collectors
- Webhook-to-Telegram bridge
- Package tests and CI integration
