from pingram import Pingram

import os
import time

from dotenv import load_dotenv
import pytest

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''
CHAT_ID = os.getenv('CHAT_ID') or ''

@pytest.mark.skipif(not TOKEN or not CHAT_ID, reason="Missing credentials for Telegram API")
def test_send_video():
    bot = Pingram(TOKEN)
    response = bot.send_video(chat_id=CHAT_ID, path="https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/Big_Buck_Bunny_1080_10s_1MB.mp4")
    time.sleep(5)  # delay to avoid rate limit
    assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"