# V40.81 Open-Issue Alternate-Solution Report

Date: 2026-10-24
Branch: `fix/v40-81-release-data-gate`
Pull request: https://github.com/bhaveshthaker87/pro-stock-intelligence/pull/20
Commit at report creation: `26b3717a0c5aec61e0e148499b2ce90048573e60`

## Executive summary

The code-side fallback path is present for user-imported Screener CSV/XLSX data and historical OHLCV CSV data. Provider response validators and CI checks are also present. This does **not** mean that a live provider is configured or that all market-data issues are closed.

## Alternate solutions implemented in the branch

1. **Screener 403 / login unavailable**
   - Do not bypass the 403 or scrape protected pages.
   - Use the app's local CSV/XLSX import path for a user-exported Screener workbook.
   - Import validation maps recognized metrics, keeps source/period metadata where available, and rejects ambiguous symbol mapping instead of guessing.
   - Remaining: verify this workflow using a real, sanitized export from the user's Screener account and confirm the imported values on-screen.

2. **Missing fundamentals and quarterly results**
   - CSV/XLSX parsers map supported metrics and the Screener workbook parser extracts annual/quarterly rows where the workbook layout matches.
   - Missing metrics are not safe to invent; derived metrics must be labelled as derived.
   - Remaining: complete a 30-stock independent verification report comparing source, reporting period, unit, imported value and official/company value; check formulas and workbook-layout variations.

3. **Historical charts without an authorized live feed**
   - CSV importer recognizes NSE UDiFF bhavcopy-style OHLCV columns, validates OHLC relationships, sorts by timestamp and filters to the selected symbol.
   - This is a historical/EOD fallback, not intraday/live data.
   - Remaining: validate actual recent NSE bhavcopy files end-to-end in the Android UI and compare chart bars/RSI/50-DMA/200-DMA/Nadaraya-Watson calculations against a known fixture.

4. **Live price and Nifty indices**
   - Provider payload validation enforces source, timestamp, status, freshness and numeric values; gateway contract is documented.
   - No configured authorized provider gateway was present at the latest inspected workflow configuration/run.
   - Remaining: obtain/configure an authorized data provider and HTTPS gateway; test real responses. Until then, label data as EOD/historical/unavailable, never live.

5. **Corporate results/events calendar**
   - Provider event payload contract and source-link/fallback approach are documented; empty provider responses are not proof that no events exist.
   - Remaining: connect an authorized, reliable calendar feed or provide official links; verify upcoming results, board meetings and corporate actions against exchange/company announcements.

6. **Provider failure handling**
   - Native provider gateway has bounded retries for eligible GET requests, does not retry 401/403, rejects malformed/oversized responses and avoids silently using stale values.
   - Remaining: run end-to-end outage/throttling/stale/future timestamp/wrong-symbol cases against a configured gateway.

7. **Release readiness**
   - Workflow checks JavaScript syntax, Python tests, provider payload contracts, APK build, lint and emulator launch/screenshot.
   - Latest inspected workflow run: https://github.com/bhaveshthaker87/pro-stock-intelligence/actions/runs/40088565408
   - At the time inspected, unit/UI smoke tests, provider-gateway validation step, APK build, checksum/upload and Android lint had completed successfully; emulator smoke test was still in progress. This is not yet a final all-jobs-passed result.
   - Remaining: wait for the final workflow conclusion, inspect emulator output/screenshot and lint artifact, then test installation and real import flow on a physical device if available.

## Status matrix

| Area | Code-side alternate | Verified status | Remaining blocker |
|---|---|---|---|
| Screener login | User-export CSV/XLSX | Parser and automated CI checks run; real account export not yet verified | Real sanitized export and UI acceptance test |
| Fundamentals | CSV/XLSX metric import | Partial | 30-stock independent verification and formula audit |
| Quarterly results | XLSX quarterly rows | Partial | Validate periods/units across real workbook variants |
| Historical candles | NSE UDiFF/EOD CSV | Parser support present | End-to-end Android chart verification |
| Live quotes | Authorized gateway contract | Not verified/live feed not configured | Licensed feed, gateway URL, real fixtures |
| Nifty indices | Validated gateway payload contract | Not verified/live feed not configured | Authorized index data feed |
| Events calendar | Event contract and official-source fallback | Partial | Reliable feed and coverage validation |
| Resilience | Bounded retries and strict validation | CI checks run; provider E2E not run without gateway | Failure-mode tests against live gateway |
| APK release | CI build/lint/emulator workflow | APK build/lint completed in inspected run; emulator was running | Final workflow success and device verification |

## Release decision

**Do not describe V40.81 as a fully live-data-ready or production-verified release yet.** A development APK can be built, but live quotes, live index values, live intraday candles and a complete event calendar require external authorized data access. Never substitute stale/reference prices while labelling them real-time.

## Next acceptance criteria

- [ ] Real Screener XLSX/CSV import succeeds for at least 5 different companies and preserves periods/units.
- [ ] 30-stock fundamentals verification report is attached.
- [ ] Real NSE EOD CSV imports and displays correctly; mixed symbols are never merged into one candle series.
- [ ] Technical indicators match a deterministic known dataset within documented tolerances.
- [ ] Authorized gateway is configured and quote/history/indices/events/dividends payloads pass strict validation.
- [ ] All GitHub Actions steps finish successfully and artifacts are reviewed.
- [ ] Android install/launch and import flow are verified on a device/emulator.
