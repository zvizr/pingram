
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

## Benefits

• Eliminates SMTP and SMS costs
• No server or inbound infra required
• Uses only a Telegram bot token
• Lightweight and auditable codebase
• Ideal for scripts, automation, and event pings
• Seamless integration with CLI tools, logs, or system alerts

## Planned features

• Retry and error handling
• Async mode (httpx.AsyncClient)
• Message templating engine
• Std input/message collectors
• Webhook-to-Telegram bridge
• Package tests and CI integration