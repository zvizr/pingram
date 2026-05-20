"""Tests for MarkdownV2 escape helpers."""
import pytest

# --- escape_markdown_v2 (text context) -------------------------------------

def test_empty_string_returns_empty():
    from pingram import escape_markdown_v2
    assert escape_markdown_v2("") == ""


def test_plain_text_with_no_specials_unchanged():
    from pingram import escape_markdown_v2
    assert escape_markdown_v2("hello world") == "hello world"


@pytest.mark.parametrize("char", list("_*[]()~`>#+-=|{}.!"))
def test_each_text_special_char_escapes(char):
    from pingram import escape_markdown_v2
    assert escape_markdown_v2(char) == f"\\{char}"


def test_backslash_itself_escapes():
    from pingram import escape_markdown_v2
    # Input is one literal backslash; output is two literal backslashes.
    assert escape_markdown_v2("\\") == "\\\\"


def test_mixed_special_and_normal_chars():
    from pingram import escape_markdown_v2
    assert escape_markdown_v2("Hello *world*!") == "Hello \\*world\\*\\!"


def test_username_underscore_escapes():
    from pingram import escape_markdown_v2
    assert escape_markdown_v2("my_username") == "my\\_username"


def test_phone_number_with_parens_and_hyphen():
    from pingram import escape_markdown_v2
    assert escape_markdown_v2("(123) 456-7890") == "\\(123\\) 456\\-7890"


# --- escape_markdown_v2_code (inline code / pre block context) -------------

def test_code_empty_returns_empty():
    from pingram import escape_markdown_v2_code
    assert escape_markdown_v2_code("") == ""


def test_code_backtick_escapes():
    from pingram import escape_markdown_v2_code
    assert escape_markdown_v2_code("`") == "\\`"


def test_code_backslash_escapes():
    from pingram import escape_markdown_v2_code
    assert escape_markdown_v2_code("\\") == "\\\\"


def test_code_passes_through_text_specials():
    """Inside code spans, only backtick + backslash are special."""
    from pingram import escape_markdown_v2_code
    assert escape_markdown_v2_code("/tmp/x_y.txt") == "/tmp/x_y.txt"


def test_code_real_command_with_backtick():
    from pingram import escape_markdown_v2_code
    assert escape_markdown_v2_code("echo `date`") == "echo \\`date\\`"


# --- escape_markdown_v2_link_url (link URL context) ------------------------

def test_link_url_empty_returns_empty():
    from pingram import escape_markdown_v2_link_url
    assert escape_markdown_v2_link_url("") == ""


def test_link_url_closing_paren_escapes():
    from pingram import escape_markdown_v2_link_url
    assert escape_markdown_v2_link_url("https://x.com/q=(a)") == "https://x.com/q=(a\\)"


def test_link_url_backslash_escapes():
    from pingram import escape_markdown_v2_link_url
    assert escape_markdown_v2_link_url("a\\b") == "a\\\\b"


def test_link_url_passes_through_other_specials():
    """Inside link URL parens, only `)` and `\\` are special."""
    from pingram import escape_markdown_v2_link_url
    url = "https://example.com/path?q=1&_=2#frag"
    assert escape_markdown_v2_link_url(url) == url
