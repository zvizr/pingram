from pingram import Pingram

import os
import time

from dotenv import load_dotenv
import pytest

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''

@pytest.mark.skipif(not TOKEN, reason="Missing TOKEN for Telegram API")
def test_get_me():
    bot = Pingram(TOKEN)
    time.sleep(1)  # delay to avoid rate limit
    response = bot.me()
    assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"