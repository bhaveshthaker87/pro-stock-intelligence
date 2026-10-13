# Pro Stock Intelligence V40.73 — Remaining-Issues Remediation Report

Date: 2026-10-11  
Base: V40.72 provider-diagnostics source ZIP  
Release type: source upgrade candidate, **not** production-certified.

## What was audited first

- Re-opened the V40.72 ZIP and verified its CRC/integrity.
- Reviewed the Android native provider, Screener parser, provider status endpoint, CSV importer, HTML diagnostics, tests and Android build configuration.
- Ran the pre-change suite: 70 tests passed.
- Confirmed that Screener uses the existing authenticated WebView session cookie and validates the company-page structure before accepting parsed fundamentals.
- Confirmed that Moneycontrol automated extraction is explicitly disabled: the app only opens public pages and supports user-mediated permitted CSV imports.
- Confirmed no Gradle executable, Android SDK, or ADB is available in this execution environment.

## Implemented in V40.73

1. **Live Screener diagnostics now performs a real validation request** when a Screener session cookie is present. It calls the same company-page parser used for fundamentals, then reports `LIVE_COMPANY_PAGE_VALIDATED` only when the page is fetched and the expected structure is parsed. Cookie presence alone no longer masquerades as successful authentication.
2. The diagnostic response reports company name, number/names of parsed fields, fetch time, source URL and probe duration. These are diagnostics, not proof that every field is independently accurate.
3. A failed probe is reported as `LIVE_VALIDATION_FAILED` with a generic recovery message; no live data success is claimed.
4. The UI timeout for diagnostics was increased to 16 seconds to accommodate the native fetch timeouts.
5. Moneycontrol status remains explicit: public page viewing is available without login, but automated extraction is disabled until an authorized documented feed/API or explicit written permission is configured. The app does not infer data access rights from a subscription login.
6. Aligned app/client/native/CI version markers to V40.73 and Android `versionCode 72`, `versionName 40.73`.
7. Added regression tests for real Screener probe wiring and for preventing false Moneycontrol live-data claims.

## Actual test results

- `python -m pytest -q --tb=line --no-header --color=no tests`: **72 passed**.
- Python syntax compilation: to be recorded in the release run below.
- Android manifest XML: to be recorded in the release run below.
- Inline JavaScript syntax: to be recorded in the release run below.
- ZIP CRC/integrity: to be recorded in the release run below.

## Not verified / remaining release blockers

- No live Screener credentials/session were supplied to this run; the new live probe is code-reviewed and source-tested but was not executed against the user's account in this environment.
- Moneycontrol automated ingestion remains disabled. Moneycontrol's official terms prohibit automated extraction and machine-readable database use without prior express written permission: https://www.moneycontrol.com/cdata/termsofuse.php
- Screener states that it does not provide an API and documents CSV export for Premium users: https://support.screener.in/article/28-export-screen-results. The current page parser remains vulnerable to upstream HTML changes, which the new probe should detect.
- No 30-stock independent field-by-field comparison report.
- No licensed/authorized real-time quote feed validation.
- No golden OHLCV reference report proving RSI(14), SMA50/SMA200 and Nadaraya–Watson output parity.
- No Android Gradle build, Android Lint, signed APK, emulator or physical-device QA because Gradle/Android SDK/ADB are absent.
- No security/dependency scan of a built APK.

## Rating

- Source regression safety: 8.0/10
- Screener diagnostics and parser validation: 7.0/10
- Fundamental accuracy evidence across stocks: 4.5/10
- Moneycontrol automated integration: 0/10 (intentionally disabled until authorized data access is configured)
- Chart/indicator reference verification: 6.0/10
- Android release confidence: 3.5/10
- **Overall release readiness: 6.6/10**

This is not a 10/10 claim. A truthful 10/10 release requires the live provider, 30-stock reconciliation, chart golden-data, build/signing, security, and device QA gates above to pass with evidence.


## Release checks actually run

- Pytest: 72 passed in 4.92s (exit 0). The Python environment emits a separate non-fatal spreadsheet-runtime warmup warning on startup; it does not change the pytest result.
- Python compile: PASS.
- Android manifest XML parse: PASS.
- Inline JavaScript syntax: 2 non-empty inline blocks checked with `node --check`; PASS.
- CSV importer JavaScript syntax: PASS.
- Android Gradle build / Lint / APK / device QA: NOT RUN — toolchain unavailable.
