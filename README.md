# Pingram

Ultra lightweight Python wrapper for Telegram messaging using your bot - an alternative to email/sms as a costless solution to sending messages. Pingram enforces non-conversational ping esque messaging, outbound messaging is
at the core of Pingram.

## Features

- Send messages
- Uses httpx under the hood
- Simple bot initilizer

## Quickstart

```bash
pip install pingram
```

## Example

### Basic Usage

```python
from pingram import Pingram

bot = Pingram(token="<BOT_TOKEN>")
bot.send("msg", {"chat_id": 123456789, "text": "Hello World"})
```

### Sending Images

```python
bot.send("photo", 
        {"chat_id": 123456789, 
        "path": "<URL/FILE PATH>", 
        "caption": "Test Photo"})
```

### Sending Documents

```python
bot.send("doc", 
        {"chat_id": 123456789, 
        "path": "<URL/FILE PATH>", 
        "caption": "Test Doc"})
```

##  Advantages

- Eliminate internal SMTP costs and complexity
- Eliminiate internal SMS-related expenses
- Zero maintenance overheard - no servers to manage, no spam filters to fight
- Low operational complexity - works with a single Telegram bot token
- Minimal code footprint, easy to audit, integrate and exend
- Acts as an alternative transport layer for events, alerts or push messaging


## Coming Soon

- Audio, video sending methods
- Error handling and retries
- Asynchronous client
