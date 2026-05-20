"""MarkdownV2 escape helpers.

Telegram's MarkdownV2 parse mode requires backslash-escaping for different
sets of special characters depending on context. This module provides one
small function per context.

Reference: https://core.telegram.org/bots/api#markdownv2-style"""
from __future__ import annotations

__all__ = [
    "escape_markdown_v2",
    "escape_markdown_v2_code",
    "escape_markdown_v2_link_url",
]


# Frozensets avoid the raw-string-with-trailing-backslash trap and give O(1)
# membership lookup for the per-character loop.
_TEXT_SPECIAL_CHARS = frozenset("_*[]()~`>#+-=|{}.!\\")
_CODE_SPECIAL_CHARS = frozenset("`\\")
_LINK_URL_SPECIAL_CHARS = frozenset(")\\")


def escape_markdown_v2(text: str) -> str:
    """Escape text for use inside a MarkdownV2 message body.

    Escapes the full set of Telegram-special characters: `_*[]()~`>#+-=|{}.!`
    and `\\`. Not idempotent — calling twice double-escapes."""
    return _escape(text, _TEXT_SPECIAL_CHARS)


def escape_markdown_v2_code(text: str) -> str:
    """Escape text for use inside an inline code span or pre block.

    Only `` ` `` and `\\` are special in code contexts. All other MarkdownV2
    syntax characters pass through unchanged."""
    return _escape(text, _CODE_SPECIAL_CHARS)


def escape_markdown_v2_link_url(url: str) -> str:
    """Escape a URL for use inside the (...) part of a MarkdownV2 link.

    Only `)` and `\\` need escaping inside the URL portion of `[label](url)`."""
    return _escape(url, _LINK_URL_SPECIAL_CHARS)


def _escape(text: str, special_chars: frozenset[str]) -> str:
    return "".join("\\" + c if c in special_chars else c for c in text)
