import os
import time

import pytest
from dotenv import load_dotenv

from pingram import Pingram

pytestmark = pytest.mark.integration

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') or ''
CHAT_ID = os.getenv('CHAT_ID') or ''

@pytest.mark.skipif(not TOKEN or not CHAT_ID, reason="Missing credentials for Telegram API")
def test_send_doc():
    bot = Pingram(TOKEN)
    response = bot.send_doc(chat_id=CHAT_ID, path="https://bitcoin.org/bitcoin.pdf")
    time.sleep(3)  # delay to avoid rate limit
    assert response.status_code == 200, f"Telegram API returned {response.status_code}: {response.text}"