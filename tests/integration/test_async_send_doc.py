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
async def test_async_send_doc():
    async with AsyncPingram(TOKEN) as bot:
        response = await bot.send_doc(chat_id=CHAT_ID, path="https://bitcoin.org/bitcoin.pdf")
        await asyncio.sleep(3)
        assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"
