# Root Cause Analysis — V40.81 (2026-10-24)

Repository: `bhaveshthaker87/pro-stock-intelligence`
Branch: `fix/v40-81-release-data-gate`
Commit inspected: `1a0c3662ab1a795fff2e2293d91c82b1982f2320`
PR: https://github.com/bhaveshthaker87/pro-stock-intelligence/pull/20

## Executive finding

The repeated user-visible failures are not explained by an APK compilation defect. The strongest verified root cause is **the application has no configured authorized market-data gateway**, while the CI workflow still allows a green build when that gateway is absent. The build verifies that code compiles and some automated checks pass; it does not verify that real stock data is available in the app. Previous status language blurred that distinction.

This RCA is based on source inspection and GitHub Actions run #478 (run ID 40088896812). It is not a claim that all runtime failures have been reproduced on the user's physical device.

## Evidence-based root causes

### P0 — Live quote and index data are not provisioned

Evidence:
- `MainActivity.kt`: `gatewayBaseUrl()` reads `BuildConfig.PROVIDER_GATEWAY_BASE_URL`.
- `nseQuote()` explicitly throws “Authorized NSE/vendor gateway is not configured” if no HTTPS gateway is configured.
- `build-apk.yml`: missing `PROVIDER_GATEWAY_BASE_URL` emits a warning and exits successfully unless `REQUIRE_LIVE_PROVIDER_GATEWAY=true` or the manual `require_live_data` input is true.

Impact:
- A green build can be produced without working quote, Nifty/index, or authorized history data.
- No parser/UI change can create a legitimate feed or replace provider access.

Fix required:
1. Deploy or select a provider gateway whose license allows the required use.
2. Configure the repository variable `PROVIDER_GATEWAY_BASE_URL` and server-side secrets.
3. Make release validation blocking and verify real quote/history/index/events payloads, including source and timestamps.
4. Until then, clearly show “Unavailable — authorized feed not configured”; never display a stale/placeholder number as live.

### P0 — Screener login/scrape path is not a dependable data contract

Evidence:
- `MainActivity.kt` directly requests `https://www.screener.in/company/{symbol}/` and parses HTML.
- The code itself has explicit HTTP 403 and login-page errors.
- `PROVIDER_GATEWAY.md` states that there is no authorized vendor configured and that a paid website login does not by itself establish permission to extract/redistribute structured data.

Impact:
- Changes in session cookies, anti-bot/security controls, or page markup can break fundamentals and quarterly data.
- Repeated cookie/header/parser tweaks cannot guarantee this path works; a 403 must not be bypassed.

Fix required:
1. Use a supported/exported Screener CSV/XLSX path for personal data where permitted, or obtain documented authorized API/data access.
2. Treat the real exported workbook as a required acceptance fixture.
3. Surface 403 as a clear actionable status and stop retrying/reparsing as if it were valid company data.
4. Do not mark Screener login fixed until an end-to-end account-session test or supported export test passes.

### P1 — CI is checking build health, not the user's complete workflows

Evidence:
- Run #478 completed all steps, including unit/UI smoke tests, provider-gateway validation, APK build, lint, and emulator smoke test.
- The provider-gateway step is deliberately non-blocking when no gateway URL is configured.
- The workflow uploads a debug APK, lint report, and emulator screenshot, but the current evidence does not show an end-to-end test with real Screener export, a real authorized quote, an index feed, or an events feed.

Impact:
- “CI success” was mistakenly treated as proof that live market data, quarterly tables, indicators, and calendars work.
- Emulator launch alone does not prove those screens are populated correctly.

Fix required:
1. Separate build/test status from data/release readiness in the report.
2. Add deterministic fixtures for CSV/XLSX, financial metric units/periods, OHLCV, RSI, 50/200 DMA and Nadaraya–Watson values.
3. Add a Playwright/WebView-level test asserting that data cards, missing-data states, selected symbol, timestamps and charts change correctly.
4. Add a release-only gate that fails without authorized provider configuration and sanitized real payload fixtures.

### P1 — Screener-derived chart fallback can still be unavailable independently of the primary history path

Evidence:
- `index.html` calls `/api/history`, then may call `/api/screener-chart` if coverage is insufficient.
- The chart code does clear the old chart on a total failure and says no synthetic candles are shown, which is safer than fabricating bars.
- However, fallback availability depends on the same fragile Screener page access and no evidence currently proves a recent NSE UDiFF CSV has been imported and plotted end-to-end in Android.

Impact:
- Users can still see no chart/history even if chart drawing and indicators compile.
- An indicator implementation can be syntactically valid but unverified against known OHLCV values.

Fix required:
1. Use an explicitly imported NSE EOD CSV for historical-only fallback and display its date/source.
2. Validate chart bars and indicators against deterministic known data, not screenshots alone.
3. Do not use a close-only series as OHLC candles; show the existing explicit no-candles state.

### P1 — Corporate events/results calendar has no verified source coverage

Evidence:
- `PROVIDER_GATEWAY.md` defines an event payload contract, but also says an authorized feed is not configured.
- The validator intentionally says an empty event array does not prove absence of events.

Impact:
- A calendar panel can be present in the UI without being complete or current.

Fix required:
1. Configure an authorized event feed or use clearly labeled official exchange/company announcement links.
2. Test upcoming results, board meetings, dividends, splits and corporate actions against official notices.
3. Never interpret an empty provider response as “no events”.

### P2 — Fundamental calculations and factor scores are not independently validated

Evidence:
- `index.html` contains score calculations and a fallback P/E derivation from market capitalization and TTM profit.
- `csv-import.js` and the provider validator check field formats/units in part, but format validation does not prove values or periods match the source.
- The existing report acknowledges that the 30-stock independent verification report has not been completed.

Impact:
- Some cards may remain blank, or values/derived scores may be misleading if source units, reporting period, or the intended definition differ.

Fix required:
1. Build a 30-stock verification matrix with symbol, metric, source, timestamp/period, raw value, unit, normalized value, and independent comparison.
2. Test quarter-column alignment with missing cells, FY/quarter labels, crore/lakh units, negatives, and duplicate labels.
3. Keep missing values missing; label every derived value and formula.

## Why previous attempts did not fix the reported issues

1. The changes concentrated on parsing, validation, error handling, and fallback behaviour.
2. The primary external dependencies—authorized quote/index/history/event feed and a reliable permitted Screener data path—were not configured or end-to-end tested.
3. The workflow's missing-gateway branch warns but passes, allowing an APK to look release-ready when the core data source is absent.
4. Unit/smoke tests and emulator launch do not test the actual account's Screener session or compare real market values with independent sources.
5. The alternate-solution report itself listed the same uncompleted acceptance criteria. It should have been treated as an open blocker list, not evidence that the issues were fixed.

## Verified status from GitHub Actions run #478

Run: https://github.com/bhaveshthaker87/pro-stock-intelligence/actions/runs/40088896812

- Workflow job: success.
- APK debug artifact uploaded: yes.
- Android lint step: success.
- Emulator smoke test and screenshot step: success.
- Provider gateway end-to-end validation: **not established by the success status alone**. The workflow explicitly allows the missing-gateway path to pass unless configured as required.
- Real Screener account login/import: not verified.
- Real quote and Nifty feed: not verified.
- Real corporate calendar coverage: not verified.
- 30-stock independent fundamentals audit: not completed.
- Physical-device acceptance test: not established by this run.

## Release decision

**V40.81 is a build-verified development APK, not a verified live-data release. Do not claim all user issues are fixed.**

Do not merge the PR or call the release complete until all of these pass:
- [ ] Authorized HTTPS provider gateway configured and real payload checks pass.
- [ ] Quote and Nifty index source/status/as-of values are visible and correct.
- [ ] Screener-supported export/import passes on at least five real sanitized company exports, or documented authorized integration works.
- [ ] Quarterly and annual values retain the correct period and unit.
- [ ] 30-stock independent fundamentals verification report passes.
- [ ] Real NSE EOD CSV produces correct symbol-specific OHLCV bars.
- [ ] RSI, 50/200 DMA, Nadaraya–Watson envelope and buy/sell markers match deterministic fixtures within defined tolerances.
- [ ] Corporate events/results are checked against official notices and coverage is disclosed.
- [ ] End-to-end Android tests verify the visible screens, not just app launch.
- [ ] Release workflow fails if required data-source configuration or integration tests are missing.

## Inputs still needed for a complete real-world RCA

A sanitized Screener export that currently fails, plus a screenshot or short screen recording showing the failing screen and selected stock, are needed to reproduce the exact account/device path. Do not share passwords, session cookies, or tokens. A permitted provider endpoint and sanitized sample responses are required to verify live quote/index/event integrations.
