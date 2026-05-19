import os
import time

import pytest
from dotenv import load_dotenv

from pingram import Pingram

pytestmark = pytest.mark.integration

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''

@pytest.mark.skipif(not TOKEN, reason="Missing TOKEN for Telegram API")
def test_get_me():
    bot = Pingram(TOKEN)
    time.sleep(1)  # delay to avoid rate limit
    response = bot.me()
    assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"