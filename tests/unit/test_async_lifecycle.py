"""Lifecycle tests for AsyncPingram: aclose, __aenter__, __aexit__."""
from unittest.mock import AsyncMock

import pytest

from pingram import AsyncPingram


async def test_async_with_calls_aclose_on_exit(
    fake_token, telegram_base, mock_api, ok_response_factory
):
    mock_api.get(f"{telegram_base}/getMe").mock(
        return_value=ok_response_factory({"id": 1})
    )
    bot = AsyncPingram(token=fake_token)
    bot.aclose = AsyncMock(side_effect=bot.aclose)  # spy on aclose
    async with bot as ctx:
        assert ctx is bot
        await ctx.me()
    bot.aclose.assert_awaited_once()


async def test_manual_aclose_closes_client(fake_token):
    bot = AsyncPingram(token=fake_token)
    assert not bot.client.is_closed
    await bot.aclose()
    assert bot.client.is_closed


async def test_async_with_closes_client_even_on_exception(fake_token, telegram_base, mock_api):
    bot = AsyncPingram(token=fake_token)
    with pytest.raises(RuntimeError):
        async with bot:
            raise RuntimeError("simulated work failure")
    assert bot.client.is_closed
