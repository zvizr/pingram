# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-05-19

### Added
- **Retry + typed error handling.** `Pingram(token, retries=3, raise_on_error=False, timeout=10.0)` now exposes:
  - Automatic retries on transient failures (transport errors, HTTP 429, HTTP 5xx) with exponential backoff and full jitter.
  - HTTP 429 responses honour `parameters.retry_after` from the body when present.
  - Fail-fast on 400/401/403/404 — no retries when retrying cannot help.
  - Typed exception hierarchy: `PingramError`, `TransportError`, `TelegramAPIError`, `RateLimitError`. Opt in by setting `raise_on_error=True` (or per-call with `_raise=True`).
- **Per-call overrides.** Any method accepts `_raise=True/False` and `_retries=N` to override instance defaults for a single call. These kwargs are stripped before forwarding to Telegram.
- **Configurable timeout.** `timeout` is now a constructor argument (previously a hardcoded 10s literal). Default is still 10.0s.
- **Two-tier test suite.** Mocked unit tests (`respx`) run on every PR across Python 3.9–3.13. Real-API integration tests run on `main` with repo secrets.
- **GitHub Actions CI.** Lint (ruff) and unit tests on every push and PR.
- **OIDC PyPI release workflow.** `v*` tag pushes trigger a build + publish via PyPI Trusted Publishers — no API tokens to manage.
- `CHANGELOG.md`.

### Changed
- Dropped Python 3.7 and 3.8 support. Now requires Python ≥ 3.9.
- Type hints modernised to 3.9+ syntax (`dict[str, Any]`, `str | None`).
- README "Tests" section now describes the two-tier setup honestly.
- "Planned features" section becomes "Roadmap" with shipped items checked off.

### Removed
- `src/pingram.egg-info/` and `.DS_Store` no longer tracked in the repo.

### Compatibility
- Existing 0.3.x code that calls `Pingram(token=...)` and inspects returned `httpx.Response` objects runs unchanged. The default `raise_on_error=False` preserves the 0.3.4 contract bit-for-bit.

## [0.3.4] - 2026-01-24
- Improved error handling.

## [0.3.3] - 2026-01-22
- PyPI re-build.

## [0.3.2] - 2026-01-21
- Maintenance release.

## [0.3.1] - 2026-01-21
- Maintenance release.

## [0.3.0] - 2026-01-21
- Photos and documents support.

## [0.2.0] - 2026-01-19
- Refactor for PyPI packaging.

## [0.1.0] - 2026-01-18
- Initial public release.
