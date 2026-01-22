from pingram import Pingram

import os
import time

from dotenv import load_dotenv
import pytest

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''
CHAT_ID = os.getenv('CHAT_ID') or ''

@pytest.mark.skipif(not TOKEN or not CHAT_ID, reason="Missing credentials for Telegram API")
def test_send_audio():
    bot = Pingram(TOKEN)
    response = bot.send_audio(chat_id=CHAT_ID, path="https://www.myinstants.com//media/sounds/hello-friend-mr-robot.mp3")
    time.sleep(3)  # delay to avoid rate limit
    assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"