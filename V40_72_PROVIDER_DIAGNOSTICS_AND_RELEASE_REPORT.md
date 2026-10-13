# Pro Stock Intelligence V40.72 — Provider Diagnostics & Release Report

**Audit date:** 2026-10-11  
**Base:** Existing V40.71 source, audited before editing.  
**Artifact:** Source ZIP; not an APK.  

## Executive verdict

V40.72 improves provider transparency and makes the Moneycontrol/Screener status explicit in the app. It adds a provider diagnostics endpoint and UI, keeps the existing Screener in-app login flow, and gives one-tap access to public stock pages at both sites. It does **not** implement automatic Moneycontrol data ingestion. That remains deliberately disabled until an authorized documented feed/API or written permission is provided.

**Overall release readiness: 6.5/10. Not production-certified and not 10/10.**

## Audit findings before editing

1. Screener fundamental data already uses the app's WebView session cookie and parses a company page. Session-cookie detection by itself is not proof that the server accepts the session; a protected request must succeed.
2. Moneycontrol was not integrated. Existing app code accurately marked it as not integrated.
3. User asked to remove any Moneycontrol login requirement. Public Moneycontrol pages can be opened without login, but viewing access is not equivalent to permission to automate extraction or build a machine-readable database.
4. The UI did not provide one clear diagnostics view that distinguishes Screener session status from Moneycontrol public-view access and automated-feed status.
5. No authorized Moneycontrol feed/API schema or written permission was supplied; no real provider payload could be tested.

## Changes implemented

- Added native `/api/providers/status?symbol=...` diagnostics.
- Diagnostics show Screener cookie detection separately from protected-request validation; no false claim that the cookie alone validates the login.
- Diagnostics show Moneycontrol public-view status separately from data-ingestion status. Public pages require no login for viewing, but automatic ingestion is explicitly `DISABLED_NO_AUTHORIZED_FEED_CONFIGURED`.
- Added UI provider-status panel with refresh, Open Moneycontrol stock search, and Open Screener company-page actions.
- Preserved the existing Screener Login button and authenticated session path.
- Preserved user-mediated CSV imports for exports the user is authorized to use.
- Aligned UI, native engine, build version, and CI artifact names to V40.72 / versionCode 71.
- Added regression tests to ensure Moneycontrol is not falsely represented as automatically integrated and that Screener cookie detection is not treated as full session validation.

## Actual checks

- `python -m pytest -q tests`: **70 passed**.
- `python -m unittest discover -s tests -q`: PASS (exit 0; OK).
- `python -m py_compile tools/*.py tests/*.py`: **PASS**.
- `node --check` on inline JavaScript blocks: **PASS**.
- `node --check app/src/main/assets/csv-import.js`: **PASS**.
- Android manifest XML parse: **PASS**.
- Release version markers: V40.72 / versionCode 71.
- ZIP integrity: checked at packaging.

## Not run / not verified

- Live Screener authenticated smoke test using the user's actual session.
- 30-stock field-by-field data comparison at a shared cutoff.
- Moneycontrol automatic data integration: no authorized feed/API contract or written permission was provided.
- Indicator parity (RSI, SMA50/SMA200, Nadaraya–Watson) against an independent golden OHLCV dataset.
- Gradle/Kotlin build, Android Lint, signed APK, emulator and real-device tests. This environment has Java but no Gradle executable, Android SDK, or ADB.
- Provider outages, rate limiting and stale-response tests against a real licensed feed.

## Evidence-based ratings

| Area | Rating | Reason |
|---|---:|---|
| UI / feature breadth | 7.5/10 | Extensive dashboard and source diagnostics added; all flows still need device QA |
| Screener session integration | 6.5/10 | Existing cookie-based page access retained; actual authenticated account not live-tested |
| Screener fundamentals accuracy across all stocks | 4.5/10 | No independent 30-stock reconciliation or current authenticated fixture set |
| Moneycontrol public-view access | 8.0/10 | Public search/company page can be opened without a Moneycontrol login |
| Moneycontrol automated data integration | 0/10 | No authorized feed/API configured; no automated extraction implemented |
| Cross-source reconciliation | 5.0/10 | CSV fallback and mismatch labels exist; live cross-source period/unit comparison is not proven |
| Chart / indicator verification | 6.0/10 | Chart UI and regression coverage exist; golden-data parity is missing |
| Automated tests | 8.5/10 | 70 local tests passed, including browser UI smoke tests |
| Android release confidence | 3.5/10 | No Gradle build, lint, APK install or device test in this environment |
| **Overall release readiness** | **6.5/10** | Better transparency and tests, but live provider evidence and Android release evidence are missing |

## Why Moneycontrol is not automatically scraped

Moneycontrol's official terms, clause 4.4, restrict automated extraction and machine-readable database use without prior express written permission; clause 4.5 says other use may require prior written consent and a separate fee. A public page that does not require login does not override these restrictions. Official source: https://www.moneycontrol.com/cdata/termsofuse.php

Screener's official support says it does not provide APIs and offers CSV export as a Premium feature: https://support.screener.in/article/28-export-screen-results

## Exact next steps to reach release quality

1. Continue using the current Screener session integration; run a live authenticated test with several symbols and save sanitized, period-labelled fixtures.
2. Provide a documented Moneycontrol feed/API contract or written permission for automated extraction, including fields, polling frequency, display/storage rights, and rate limits. If only an allowed export is available, use the existing import workflow instead of claiming automated live integration.
3. Implement the adapter against that authorized schema, with source-specific timestamps, fiscal periods, units, symbol mapping, timeout/retry/cache policy and explicit stale/unavailable states.
4. Reconcile at least 30 stocks across large/mid/small caps and banks; record every discrepancy and explain whether it is period, unit, timing, or true-value mismatch.
5. Verify RSI(14), SMA50, SMA200 and Nadaraya–Watson outputs against independent reference calculations and test for look-ahead/repainting.
6. Run the provided CI workflow to build, lint, install and launch the APK on an emulator; complete a real-device rotation/offline/session-expiry test.
7. Re-rate only after these release gates have evidence.

**Bottom line:** V40.72 is an improved source candidate with 70 passing tests and honest provider diagnostics. It does not yet deliver fully automated live data from both providers and should not be rated 10/10 until the missing authorization, live-data, and Android release evidence is supplied.
