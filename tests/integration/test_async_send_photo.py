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
async def test_async_send_photo():
    async with AsyncPingram(TOKEN) as bot:
        response = await bot.send_photo(
            chat_id=CHAT_ID,
            path="https://i.pinimg.com/736x/7e/88/e2/7e88e27cfca500ef5d60fc03ddab8d04.jpg",
        )
        await asyncio.sleep(3)
        assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"
