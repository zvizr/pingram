from pingram import Pingram

import os
import time

from dotenv import load_dotenv
import pytest

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''
CHAT_ID = os.getenv('CHAT_ID') or ''

@pytest.mark.skipif(not TOKEN or not CHAT_ID, reason="Missing credentials for Telegram API")
def test_send_message():
    bot = Pingram(TOKEN)
    response = bot.message(chat_id=CHAT_ID, text="Test")
    time.sleep(1)  # delay to avoid rate limit
    assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"