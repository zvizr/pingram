from pingram import Pingram

import os
import time

from dotenv import load_dotenv
import pytest

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''
CHAT_ID = os.getenv('CHAT_ID') or ''

@pytest.mark.skipif(not TOKEN or not CHAT_ID, reason="Missing credentials for Telegram API")
def test_send_photo():
    bot = Pingram(TOKEN)
    response = bot.send_photo(chat_id=CHAT_ID, path="https://i.pinimg.com/736x/7e/88/e2/7e88e27cfca500ef5d60fc03ddab8d04.jpg")
    time.sleep(3)  # delay to avoid rate limit
    assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"    