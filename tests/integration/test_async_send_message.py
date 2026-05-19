import asyncio
import os

import pytest
from dotenv import load_dotenv

from pingram import AsyncPingram

pytestmark = pytest.mark.integration

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''
CHAT_ID = os.getenv('CHAT_ID') or ''


@pytest.mark.skipif(not TOKEN or not CHAT_ID, reason="Missing credentials for Telegram API")
async def test_async_send_message():
    async with AsyncPingram(TOKEN) as bot:
        response = await bot.message(chat_id=CHAT_ID, text="Async test")
        await asyncio.sleep(1)
        assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"
