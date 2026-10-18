# V40.81 Deep Audit and Completion Plan

Audit date: 2026-10-18
Working branch: fix/v40-80-provider-gateway-validation
PR: https://github.com/bhaveshthaker87/pro-stock-intelligence/pull/18
Latest reviewed commit: a4c8d93ce8ffbb915796ab93240afcd5fe20e20b

## Executive decision
Do not publish V40.80 as a fully accurate production release yet. Latest CI runs #402/#403 are still in progress at the time of this audit. Provider gateway E2E is blocked until an authorized provider and HTTPS gateway are deployed and configured. Screener login/cookie presence alone does not prove company ratios were fetched or that automated extraction is permitted.

V40.81 should be a reliability/data-quality release first, not a visual-only version bump. Keep PR #18 draft until P0 acceptance criteria are met.

## Audit findings
- Latest commit adds a ratio snapshot UI and extra CSV/header mappings, plus strict numeric/unit checks.
- Automated tests exist for CSV parsing, chart-row normalization, release regressions, provider payload validation, security gates, factor-score backtests and a 30-stock comparison report.
- Latest Android emulator smoke test is still running in CI; its screenshot/log result has not been reviewed in this audit.
- Duplicate workflow runs exist for the same commit; use the newest authoritative run and avoid generating extra runs unnecessarily.
- The ratio snapshot UI displays fields supplied by the current data object. It does not itself fetch missing data. Missing fields must remain Not available.
- Screener parsing depends on returned page markup and may have low coverage when markup changes, session expires, or the server returns a login/403 page.
- PROVIDER_GATEWAY.md explicitly says no licensed vendor is configured; CI skips live E2E if PROVIDER_GATEWAY_BASE_URL is unset.
- Existing test_stock_verification_report.py exercises a synthetic comparison fixture; it is not evidence that 30 real stocks have been verified.
- CSV tests cover several fields, but production validation still needs real, permitted samples with confirmed column labels, periods and units.
- Screener login/session and public Moneycontrol website access do not by themselves grant API or multi-user redistribution rights.
- Broad NSE/BSE search and official security-master completeness remain limitations; local symbol lookup is not an exhaustive exchange master.
- A successful APK build is not proof of live price freshness, corporate events, correct indicators, or multi-user production readiness.

## V40.81 work plan and exit criteria

### Gate 0 — Freeze and reproduce (P0)
1. Wait for the latest commit CI to finish. Save job summary, test results, APK checksum, lint output, emulator screenshot and logcat.
2. If any job fails, reproduce it, fix the root cause and add a regression test before proceeding.
3. Run the full Python/Node test suite and Android lint/build against one exact commit SHA.
4. Check version markers, package/versionCode alignment and artifact names.
Exit: all automated checks green on the same SHA; screenshot is visually inspected; no untriaged failures.

### Gate 1 — Prove the Screener data path (P0)
1. In the app, run diagnostics for TCS and INFY. Capture status code, final URL/host, page classification, parser coverage, source URL, fetched timestamp and sanitized error only—never cookies/session tokens.
2. Confirm whether each request returns company ratios, a login page, a challenge, HTTP 403, or a valid page with changed markup.
3. For a valid permitted page, map each visible label/value from the same ratio row; keep unknown fields null and attach provenance/period.
4. For 401/403/challenge/changed markup, stop parsing and surface a clear actionable status. Do not evade access controls or rotate cookies/proxies to bypass them.
5. Document the supported fallback: user-selected Screener CSV export with required NSE Code and chosen metrics; show import time, report period, units and field coverage.
Exit: TCS and INFY pass repeatable integration tests using authorized page access or documented CSV import; at least 90% of requested ratio fields in the supplied export map correctly; no silent fabricated values.

### Gate 2 — Ratio mapping and 30-stock reconciliation (P0)
1. Build a sanitized reference set for 30 NSE stocks from permitted exports/source data.
2. Compare CMP/reference close (label separately), market cap, P/E, EPS, book value, dividend yield, ROCE, ROE, OPM, industry P/E, face value, PEG, Piotroski, promoter/public/pledged holdings, DMA50/200, RSI, sales growth and profit growth/variance.
3. Record symbol, metric, unit, period, as-of, source, reference value, app value, absolute/relative variance and disposition.
4. Never compare metrics with different reporting periods or incompatible units. Flag rounding tolerance explicitly.
5. Test Cr, Lakh, commas, parentheses negatives, zero, dash/N/A, duplicate columns, alternate labels, missing periods and ambiguous currency/unit.
Exit: 30/30 stocks have a traceable source and matching periods; every discrepancy is explained or marked failed; no unknown unit silently accepted.

### Gate 3 — Live quote, index and OHLCV provider (external P0)
1. Obtain a provider contract/API specification that explicitly permits in-app display, history, caching and intended user count/redistribution.
2. Deploy an HTTPS server-side gateway; provider keys remain server-side. Configure PROVIDER_GATEWAY_BASE_URL in GitHub Actions and the app build environment.
3. Use documented provider endpoints only; no invented APIs, unauthorized scraping, or protected-page bypass.
4. Run real sanitized fixtures and live smoke tests for quote, history, NIFTY 50, NIFTY BANK, NIFTY IT, dividends and corporate events.
5. Test wrong symbol, stale/future timestamps, wrong timezone, delayed/EOD label, 401/403/429/5xx, timeout, empty result and partial/malformed response.
6. UI must distinguish REALTIME, DELAYED, EOD, USER_IMPORTED, STALE and UNAVAILABLE; never call an imported closing price a live quote.
Exit: source + provider timestamp + status are visible for each market value; actual end-to-end tests pass. If provider authorization/gateway is unavailable, this gate remains BLOCKED and the app must disclose it.

### Gate 4 — Charts and indicators (P1)
1. Validate OHLCV against a known permitted sample; validate timezone, duplicate candles, gaps, volume and corporate-action adjustments.
2. Compare SMA50/SMA200, RSI(14), Nadaraya–Watson Envelope and buy/sell triangles against independent reference calculations on fixed datasets.
3. Test short history, flat prices, split/gap data, zero volume and malformed bars; disable signals when minimum history is missing.
4. Verify zoom, crosshair, resize, fullscreen, landscape and responsive layouts on emulator/device.
Exit: indicator results match the documented algorithm within stated tolerance; no chart claims live when source is imported or EOD.

### Gate 5 — Fundamental score and recommendations (P1)
1. Inspect factor score inputs, weights, missing-data behavior and look-ahead bias.
2. Use point-in-time fundamentals for backtests, include delisted/survivorship limitations and transaction-cost/slippage assumptions.
3. Verify score is coverage-adjusted; missing metrics must not silently improve a stock score.
4. Show score timestamp, source coverage, risk label and explanation for each factor.
Exit: deterministic test fixtures, documented score formula and reproducible backtest report; no investment guarantee claims.

### Gate 6 — Security and multi-user (P1)
1. Confirm no secrets/cookies/tokens in repo, APK, logs or artifacts.
2. Deploy authenticated gateway with per-user access control, rate limits, request size/time limits, bounded retries, audit logs and secret rotation.
3. Test tenant isolation, unauthorized access, expired/revoked sessions, rate limiting and provider outage.
4. Do not share a personal m.Stock account/API key across all app users. Use official per-user consent/partner integration if applicable.
5. Review data-source licensing and privacy disclosure for all intended users.
Exit: security checklist passes; no credential leakage; multi-user data isolation demonstrated.

### Gate 7 — Release candidate (P2)
- Clean build from tagged commit.
- Automated tests, Android lint, emulator install/launch/screenshot, artifact checksum.
- Visual check of ratio snapshot on narrow and wide screens.
- Release notes list source, freshness, unavailable features and known limitations.
- Keep draft until all mandatory gates pass; publish only a verified release candidate.

## Progress reporting model
Report each area separately: code/parsing; automated CI/build; Screener/CSV data path; authorized live provider; 30-stock reconciliation; chart/indicator validation; security/multi-user; release evidence.
100% means all applicable acceptance criteria pass with artifacts/evidence. External licensing, provider credentials and production deployment cannot be marked complete by code edits alone.

## Immediate next actions
1. Review latest CI runs #402/#403 and inspect emulator screenshot/logs.
2. Fix any failing test before making further UI changes.
3. Run TCS/INFY Screener diagnostics and capture sanitized result classification.
4. If blocked by 403 or permission limits, prioritize robust CSV import and source/period metadata rather than bypassing the block.
5. Collect a permitted 30-stock reference export; generate the real comparison report.
6. Only after these results, implement the next code changes under V40.81.