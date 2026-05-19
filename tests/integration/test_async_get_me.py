import asyncio
import os

import pytest
from dotenv import load_dotenv

from pingram import AsyncPingram

pytestmark = pytest.mark.integration

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''


@pytest.mark.skipif(not TOKEN, reason="Missing TOKEN for Telegram API")
async def test_async_get_me():
    async with AsyncPingram(TOKEN) as bot:
        await asyncio.sleep(1)  # delay to avoid rate limit
        response = await bot.me()
        assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"
