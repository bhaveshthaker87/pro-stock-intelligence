# Pro Stock Intelligence V40.61 — Deep Audit Report

**Date:** 2026-10-11  
**Status:** Source hardening candidate; not production-certified.  
**Version:** `40.61` / Android `versionCode 60`

## Fixes made in V40.61

1. **Quote timestamp integrity:** the NSE public website adapter no longer writes the local response-receipt time into `priceTimestamp`. The response receipt is stored as `responseReceivedAt`; the UI does not present it as the provider's quote timestamp. If the provider does not expose an actual quote timestamp, the UI says so.
2. **Removed overconfident UI labels:** replaced claims such as “LIVE QUOTE”, “VERIFIED-FIRST”, and “Verified exchange + Screener HTTP” with source-aware / freshness-unverified language. The app distinguishes a returned price from a certified live quote.
3. **Corporate-event absence is not treated as proof:** an empty Yahoo Finance event response now explicitly says that no returned event does not establish that no event exists. The official exchange/company filings still need to be checked.
4. **Screener session claims:** the dividend scan wording now says the session response was parsed but authentication validity and field freshness are not independently certified; results are first-page only.
5. **Response hardening:** API responses use `no-store`, `Pragma: no-cache`, `X-Content-Type-Options: nosniff`, and a same-origin `Access-Control-Allow-Origin` instead of a wildcard.
6. **Out-of-sample harness:** `tools/factor_score_backtest.py` accepts `--oos-start` and reports metrics only on/after that holdout cutoff. It labels full-sample runs exploratory, uses a configurable 25 bps default all-in turnover-cost assumption, and warns when fewer than 24 evaluation periods are available.
7. **Release metadata:** HTML, native health endpoint, Gradle version metadata, tests, and workflow artifact names aligned to V40.61.
8. **Regression coverage:** added checks for timestamp honesty, source labels, response headers, OOS date filtering, insufficient OOS periods, and release version consistency.

## Local validation results

| Check | Result |
|---|---|
| `python -m pytest -q` | **PASS — 21 passed** |
| CI-equivalent `python -m unittest discover -s tests -v` | **PASS — 21 tests** |
| Inline JavaScript syntax (`node --check`) | **PASS — 2/2 script blocks** |
| Android manifest XML / workflow YAML | **PASS — both parse** |
| ZIP integrity / SHA-256 | PASS — checksum published in the summary |
| Gradle APK build / emulator launch | **NOT RUN locally** — Gradle, Android SDK and ADB are absent |
| Live data-provider contract / source timestamps | **NOT certified** — no licensed vendor account, API credentials, or provider agreement supplied |
| Upcoming-results/corporate-action calendar | **NOT integrated as a verified live feed** — official links remain; no dates are fabricated |
| Genuine strategy performance | **NOT established** — no point-in-time historical score dataset, future returns, or survivorship-aware universe supplied |

## Unresolved blockers that require an external dependency

### Authorized market data

The existing NSE website endpoint is best-effort web access, not proof of a licensed real-time feed. Yahoo Finance is third-party fallback data. To complete a proper integration, select a provider and supply a subscription/account and supported API/feed contract. Keep credentials on a server-side gateway; do not embed a vendor secret in the APK. The native app currently has no deployed gateway URL to connect to.

Official NSE references:
- Real-time data subscription and authorized-vendor information: https://www.nseindia.com/static/market-data/real-time-data-subscription
- NSE data usage and sharing policy: https://www.nseindia.com/static/market-data/nse-data-policy
- Paid corporate data: https://www.nseindia.com/static/market-data/corporate-data-subscription

### Corporate calendar

NSE's official calendar and results pages are linked in the UI, but the standalone app does not embed a supported, authorized structured feed. A complete fix requires an authorized provider endpoint/schema and terms permitting the intended use. Empty results are not interpreted as “no event”.

### Out-of-sample research

The new holdout mode improves separation of evaluation dates, but it does not generate historical factor scores, verify data timestamps, prove delisted-stock inclusion, or guarantee realistic corporate-action-adjusted returns. No strategy performance claim is made until a documented point-in-time dataset is provided and evaluated.

### Android build/runtime

The workflow is configured to build the APK, install it in an Android emulator, launch the app, capture a screenshot, and fail on fatal runtime exceptions. It has not been executed in this workspace; a workflow file is not proof of a successful build. A successful CI run and device/emulator log review remain mandatory.

## Regression scope and security limitations

The Playwright suite uses deterministic mocked provider responses. It exercises the six main tabs, five saved query cards, stock analysis flow, chart controls, watchlist/alerts, safe-link handling, mobile width, version handshake, source wording, and selected failure/data-integrity conditions. It is not a test of real provider correctness, every possible symbol/query, exhaustive browser accessibility, penetration testing, or every Android lifecycle path. No third-party security certification is claimed.

The app still contains a monolithic native provider and a large single-page HTML asset. A full module split, signed production release, dependency/SBOM audit, and independent security assessment remain future work after the data contract is finalized.

## Release decision

V40.61 improves data provenance, false-confidence wording, response headers, backtest holdout support, and regression coverage. It is **not a 10/10 or production release** because live authorized-provider integration, structured corporate events, real dataset-based out-of-sample validation, and Android build/runtime evidence remain open. Those cannot be truthfully completed without provider access/data and a successful Android CI/device run.
