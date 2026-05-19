# Pingram 0.4.0 — Revival Release Design

**Status:** Approved for implementation
**Target version:** 0.4.0
**Previous release:** 0.3.4 (2026-01-24)

---

## Context

Pingram is a minimal sync Python wrapper for sending outbound Telegram messages via the Bot API. Single-file core, depends only on `httpx`, ~20 KB. The last release shipped on 2026-01-24; pip downloads have roughly quadrupled (from ~1k to ~4k) in the four months since, but no commits have landed in that window. The goal of 0.4.0 is to visibly resume maintenance with a release that has real substance — not a cosmetic version bump — while breaking zero existing installs.

## Goals

1. Ship a heartbeat release that defensibly signals "alive and maintained"
2. Deliver the highest-value item on the README's existing "Planned features" list: **retry + error handling**
3. Establish CI on every PR so future contributions land safely and the README earns its first green badge
4. Establish OIDC-based PyPI release infrastructure so subsequent releases ship in one tag push
5. Maintain 100% backward compatibility — `pip install -U pingram` from any 0.3.x must produce identical behaviour by default

## Non-Goals (deferred to 0.5.0+)

- Async support (`AsyncPingram`)
- Message templating engine
- Webhook-to-Telegram bridge
- Stdin / message collectors
- API breaking changes (reserved for a future 1.0)
- Documentation site (sphinx / mkdocs)
- Type stubs / `py.typed` marker
- Python 3.14 support

## Architecture

### Module layout

```
src/pingram/
├── __init__.py        # public re-exports: Pingram + exception types
├── pingram.py         # Pingram class (existing, lightly modified)
├── _errors.py         # exception hierarchy (~30 lines)
└── _retry.py          # retry policy + executor (~80 lines)
```

Underscore-prefixed module names mark internals — only the public exception types are re-exported from `__init__.py`. This preserves freedom to refactor internals without breaking imports.

### Exception hierarchy

```
PingramError(Exception)
├── TransportError        # network / connection / timeout
└── TelegramAPIError      # non-2xx response from Telegram
    └── RateLimitError    # 429 specifically
```

Attributes:

- `TelegramAPIError.status_code: int`
- `TelegramAPIError.description: str | None` — from Telegram's response body `description` field
- `TelegramAPIError.response: httpx.Response` — raw response for advanced inspection
- `RateLimitError.retry_after: float | None` — from response body `parameters.retry_after`
- `TransportError.__cause__` — the originating `httpx.RequestError` is preserved

### Retry policy

Default config: 3 attempts (1 initial + 2 retries), exponential backoff with jitter, ~7 s max total backoff.

**Retryable conditions:**

- `httpx.ConnectError`, `httpx.ReadTimeout`, `httpx.WriteTimeout`, `httpx.PoolTimeout`
- HTTP 429 — honour `parameters.retry_after` from response body when present, else fall back to exponential backoff
- HTTP 5xx (server error)

**Non-retryable — fail fast:**

- HTTP 400 (bad request: wrong payload, retry won't help)
- HTTP 401 (unauthorized: invalid token)
- HTTP 403 (forbidden: bot blocked, chat not found)
- HTTP 404 (not found: wrong endpoint)

When `retries=0`, no retries are attempted — bit-for-bit identical to 0.3.4 behaviour.

### Public API surface

Constructor signature (all new parameters optional and keyword-only):

```python
class Pingram:
    def __init__(
        self,
        token: str,
        *,
        retries: int = 3,
        raise_on_error: bool = False,
        timeout: float = 10.0,   # newly configurable; 10s was hardcoded in 0.3.4
    ):
        ...
```

The 10 s timeout was previously a hardcoded literal inside `_get`/`_post`. Promoting it to a constructor parameter while keeping `10.0` as the default preserves existing behaviour.

**Per-call override mechanism:** kwargs prefixed with `_` are stripped before forwarding to Telegram's API (the current `**kwargs` forwarding pattern is preserved). Recognised underscore-kwargs:

- `_raise: bool` — overrides constructor `raise_on_error` for this call
- `_retries: int` — overrides constructor `retries` for this call

**Example:**

```python
from pingram import Pingram, PingramError, RateLimitError

bot = Pingram(token="...", raise_on_error=True, retries=5)

try:
    bot.message(chat_id=123, text="hello")
except RateLimitError as exc:
    sleep(exc.retry_after or 1)
    bot.message(chat_id=123, text="hello")
except PingramError:
    log.exception("send failed")
```

### Behaviour matrix

| `raise_on_error` | On success | On Telegram error (after retries) | On transport error (after retries) |
|---|---|---|---|
| `False` (default) | returns `httpx.Response` | returns failed `httpx.Response` | re-raises the original `httpx.RequestError` (matches 0.3.4) |
| `True` | returns `httpx.Response` | raises `TelegramAPIError` / `RateLimitError` | raises `TransportError` (wraps the `httpx.RequestError` as `__cause__`) |

0.3.4 lets `httpx` exceptions propagate naturally on transport failure; the `raise_on_error=False` path preserves that exact contract.

## Test reorganisation

```
tests/
├── conftest.py                    # registers `integration` pytest marker
├── unit/                          # respx-mocked, runs in CI, no secrets
│   ├── conftest.py                # respx fixtures, fake bot token
│   ├── test_send_message.py
│   ├── test_send_photo.py
│   ├── test_send_doc.py
│   ├── test_send_audio.py
│   ├── test_send_video.py
│   ├── test_get_me.py
│   ├── test_retry.py              # NEW — 429 retry-after, backoff, max-attempts, fail-fast
│   └── test_errors.py             # NEW — raise_on_error paths, exception type mapping
└── integration/                   # MOVED from current tests/test_*.py
    ├── conftest.py                # requires .env with BOT_TOKEN + CHAT_ID
    └── test_*.py                  # existing 6 files, decorated @pytest.mark.integration
```

Pytest configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests/unit"]
markers = [
    "integration: real-API tests; require BOT_TOKEN + CHAT_ID env vars",
]
```

Default-discovery behaviour:

- `pytest` → runs `tests/unit/` only (CI default, contributor default)
- `pytest tests/integration -m integration` → runs the real-API suite (maintainer + nightly main CI)

## CI workflows

### `.github/workflows/ci.yml`

**Triggers:** `push` to any branch + `pull_request`.

**Jobs:**

1. `lint` — Python 3.12, `ruff check src/ tests/`
2. `test` — matrix `[3.9, 3.10, 3.11, 3.12, 3.13]` on `ubuntu-latest`
   - `pip install -e .[dev]`
   - `pytest tests/unit -v`
   - Pip cache keyed on `pyproject.toml` hash

Adds CI badge to README: `![CI](https://github.com/zvizr/pingram/actions/workflows/ci.yml/badge.svg)`.

### `.github/workflows/integration.yml`

**Triggers:** `push` to `main` only.

Single job, Python 3.12, runs `pytest tests/integration -m integration` with `BOT_TOKEN` + `CHAT_ID` from repo secrets. Does not run on PRs (Telegram secrets aren't exposed to fork PRs anyway). Failures notify the maintainer but don't block the PR pipeline.

### `.github/workflows/release.yml`

**Triggers:** `push` of a tag matching `v*`.

Job:

- Python 3.12
- `pip install build`
- `python -m build` (wheel + sdist into `dist/`)
- `pypa/gh-action-pypi-publish@release/v1` with OIDC trusted publishing

**One-time PyPI setup:** add a Trusted Publisher for `zvizr/pingram` with workflow `release.yml`. After that, no API tokens to manage or rotate.

## Housekeeping

### `pyproject.toml` changes

- `version = "0.4.0"`
- `requires-python = ">=3.9"` (was `>=3.7`)
- Add classifiers: `Programming Language :: Python :: 3.9` … `3.13`, `Topic :: Communications :: Chat`, `Development Status :: 4 - Beta`
- Add `respx` to `[project.optional-dependencies].dev`
- Add `[tool.pytest.ini_options]` block per the Test reorganisation section
- Add `[tool.ruff]` block with conservative defaults (line-length 100, target Python 3.9)

### `.gitignore` additions

```
.DS_Store
.pingram-dev.py
dist/
*.egg-info/
.venv/
__pycache__/
.pytest_cache/
.env
```

Plus a one-time `git rm --cached` pass to remove already-tracked junk: `.DS_Store`, `src/pingram.egg-info/`.

### Source modernisation in `pingram.py`

Replace `Optional[str]` → `str | None`, `Dict[str, Any]` → `dict[str, Any]`, etc. Drop now-unused `from typing import Optional, Dict, ...` imports. Safe to do once `requires-python` is bumped to 3.9+.

### `CHANGELOG.md` (new file, Keep-a-Changelog format)

Documents 0.4.0 in detail. Includes one-line retroactive entries for 0.3.0–0.3.4 derived from existing git log so the file isn't bizarrely empty before 0.4.0.

### README updates

- Add CI badge alongside existing badges
- Rewrite the "no mocks" claim honestly: two-tier test setup (mocked units + opt-in real-API integration)
- New `## Error handling` section with typed-exception examples and the behaviour matrix
- Convert `## Planned features` → `## Roadmap` with `[x]` for shipped items (retry/errors, CI) and `[ ]` for remaining
- Footer note: *"Maintained — issues and PRs welcome."*

## Release sequence

1. Create branch `release/0.4.0` from `main`
2. Implement all changes per the implementation plan that follows this design
3. Open PR — CI must go green across all 5 Python versions
4. Merge PR to `main`
5. Configure PyPI Trusted Publisher (one-time, manual on pypi.org)
6. Tag `v0.4.0` on `main` and push → release workflow auto-publishes to PyPI
7. Manually create GitHub Release from the tag, paste CHANGELOG entry as body
8. Optional: short post on r/Python "Showcase Saturday" or equivalent channel — *"pingram 0.4.0: retry, typed errors, CI, still 20 KB"*

## Risk assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| New default retry behaviour surprises a user who relied on instant-fail timing | Low | `raise_on_error=False` default + return-Response on exhausted retries matches the failure mode 0.3.4 already exposed (a non-2xx Response). Documented in CHANGELOG. |
| respx mocks drift from real Telegram API shape over time | Medium-low | Integration suite still runs on every push to main and catches drift within a day of a Telegram-side change |
| Trusted Publisher mis-setup blocks release | Low | One-time setup; test by tagging `v0.4.0-rc1` first if paranoid |
| Type-hint modernisation accidentally lands without the 3.7/3.8 drop | Low | All changes ship atomically in the same PR |
| 4k existing installs hit an unexpected behavioural change | Low | Backward-compat is the headline non-goal; manually verify with a sample script that exercises `bot.message`, `bot.send_photo`, `bot.me` against the new release before tagging |

## Success criteria

- `pip install pingram==0.4.0` succeeds from a clean environment on Python 3.9, 3.10, 3.11, 3.12, 3.13
- Existing 0.3.x code runs unchanged against 0.4.0 (verified manually + via the integration suite passing)
- README displays a green CI badge
- PyPI publish via tag push works end-to-end without manual `twine upload`
- At least three user-visible improvements over 0.3.4: retry, typed errors, CI/release automation
