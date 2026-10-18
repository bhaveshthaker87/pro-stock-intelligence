# V40.80 Release Readiness Plan

Updated: 2026-10-18
Branch: `fix/v40-80-provider-gateway-validation`
Pull request: https://github.com/bhaveshthaker87/pro-stock-intelligence/pull/18

## Status rule

A feature counts as complete only when its code is present and its test/evidence passes. A successful Android build is not proof of live market data. A missing gateway must be reported as **blocked/skipped**, never passed. Do not inflate the overall percentage to meet a target.

## Work completed in this remediation
- HTTPS-only configurable gateway contract; no provider secret embedded in APK.
- Strict quote/history/index/event/dividend response validation and explicit stale/unavailable handling.
- Screener 401/403 diagnostics without attempting to bypass access controls.
- Regression test suite and CI workflow for Python/UI checks, APK, lint, emulator smoke test and artifact checksums.
- This update: dividend validator now rejects zero/negative CMP and market capitalization and negative dividend yield; regression tests added for these cases and boolean numeric values.

## Remaining work and acceptance criteria

### P0 — Build, tests and app reliability
- [ ] Latest commit's CI run completes successfully (unit/UI tests, APK, checksum, Android lint and emulator smoke test).
- [ ] Inspect emulator screenshot and logs; verify home/dashboard loads, no fatal WebView/JS errors, and unavailable-data states are readable.
- [ ] Test CSV import for Screener export and OHLCV export: malformed CSV, duplicate symbols, unit ambiguity, missing periods, invalid OHLC, large file and empty file.
- [ ] Fix every reproducible failing test; retain regression coverage.

### P0 — Authorized data integration (external dependency)
- [ ] Obtain a provider agreement/API specification that explicitly permits the intended data use, history, display, caching and multi-user redistribution.
- [ ] Deploy an HTTPS gateway with provider credentials stored only server-side; configure GitHub repository variable `PROVIDER_GATEWAY_BASE_URL`.
- [ ] Validate sanitized real provider payloads for quote, OHLCV history, indices, events and dividends.
- [ ] Run live smoke tests that prove source, timestamp, status and correct symbol mapping. If the gateway is absent, these checks remain blocked, not passed.
- [ ] Verify NIFTY 50, NIFTY BANK and NIFTY IT mappings; verify no stale/reference price is labelled live.

### P1 — Fundamentals and chart correctness
- [ ] Reconcile at least 30 stocks against an authorized source/export, recording symbol, field, unit, reporting period, source, as-of date, app value, reference value and variance.
- [ ] Verify PE, EPS, CMP, market cap, ROCE, ROE, debt/equity and dividend yield parsing with missing/zero/negative/decimal/unit-suffix fixtures.
- [ ] Verify OHLCV chart calculations against known datasets: SMA 50/200, RSI(14), Nadaraya–Watson Envelope and buy/sell markers. MACD is not part of the requested chart.
- [ ] Confirm missing history disables indicators rather than drawing fabricated candles/signals.
- [ ] Validate corporate-event results against provider source and clearly distinguish “no rows returned” from “no events exist”.

### P1 — Multi-user security and privacy
- [ ] Confirm no API keys, cookies, passwords, OTPs or tokens exist in source, APK, logs or CI artifacts.
- [ ] Deploy user authentication, per-user authorization/rate limits, timeouts, bounded retries, monitoring and secret storage.
- [ ] Test user-data isolation, unauthenticated requests, expired/revoked tokens, provider 401/403/429/5xx, timeout and outage.
- [ ] Keep optional m.Stock account linking separate from the shared market-data feed; use only official partner/user-consent flow.

### P2 — Release polish
- [ ] Check responsive layout on narrow and wide screens, chart zoom/crosshair/fullscreen/landscape and table horizontal scrolling.
- [ ] Verify loading, stale, delayed, EOD, unavailable and retry states.
- [ ] Produce release notes with provider names, timestamps, known limitations and privacy/data handling.
- [ ] Generate a clean release APK, checksum, lint report, emulator evidence and final test report; only then mark the release candidate ready.

## Progress reporting
Report separate scores rather than one misleading number:
- Code/validation implementation
- Automated test/build evidence
- Live provider integration
- Fundamentals/chart data verification
- Multi-user security and release readiness

Overall 100% means every applicable checkbox above has evidence, including authorized live-data E2E and production security checks. Provider authorization, gateway hosting, credentials and production deployment are external prerequisites and cannot be completed by editing Android code alone.
