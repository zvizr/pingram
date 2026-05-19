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
async def test_async_send_video():
    async with AsyncPingram(TOKEN) as bot:
        response = await bot.send_video(
            chat_id=CHAT_ID,
            path="https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/Big_Buck_Bunny_1080_10s_1MB.mp4",
        )
        await asyncio.sleep(5)
        assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"
