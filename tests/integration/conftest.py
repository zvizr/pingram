"""Integration-test fixtures.

Real-API integration tests require BOT_TOKEN and CHAT_ID environment variables
(typically loaded from a project-root .env). When either is missing, tests in
this directory are skipped rather than failing.
"""
import os

import pytest


@pytest.fixture(scope="session")
def bot_token() -> str:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        pytest.skip("BOT_TOKEN env var not set")
    return token


@pytest.fixture(scope="session")
def chat_id() -> str:
    cid = os.environ.get("CHAT_ID")
    if not cid:
        pytest.skip("CHAT_ID env var not set")
    return cid
