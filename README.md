# Pingram

Ultra lightweight Python wrapper for Telegram messaging using your bot - an alternative to email/sms as a costless solution to sending messages. Pingram enforces non-conversational ping esque messaging, outbound messaging is
at the core of Pingram.

## Features

- Send messages
- Uses httpx under the hood
- Simple bot initilizer

## Example

```python
from pingram import Pingram

bot = Pingram(token="<BOT_TOKEN>")
bot.send("msg", {"chat_id": 123456789, "text": "Hello World"})
```

## Coming Soon

- Image, document sending methods
- Error handling and retries
- Asynchronous client
