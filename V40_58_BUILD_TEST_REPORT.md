# Pro Stock Intelligence V40.58 — Build & Test Report

**Date:** 2026-10-11  
**Package:** V40.58 / Android `versionCode 57`  
**Scope:** Source audit and local automated checks. This is not a production certification.

## Changes made

1. **Version-handshake defect fixed.** V40.57's frontend expected `V40.57 DIAMOND CONSISTENCY + DATA RELIABILITY`, while the native `/api/health` handler returned `V40.57 SOURCE TRANSPARENCY + VERSION FIX`. That mismatch could cause a false “API version mismatch” warning with matching project files. V40.58 aligns both values and adds a regression test.
2. **Unsafe news URL schemes blocked.** News links now allow only absolute `http:`/`https:` URLs; `javascript:`, `data:`, malformed and other schemes resolve to `#`. Link rel includes `noopener noreferrer`. Regression checks exercise unsafe and safe URL examples in Chromium.
3. **WebView hardening.** Enabled Android WebView Safe Browsing and disabled JavaScript-opened popup windows.
4. **WebView lifecycle cleanup.** Stops loading and destroys the WebView in `onDestroy()`.
5. **Release metadata aligned.** HTML, native engine, Gradle metadata and workflow artifact names now use V40.58; Android `versionCode` is 57.
6. **Preserved transparent data labels.** The code still explicitly discloses that Moneycontrol is not integrated, Yahoo Finance is used for historical OHLCV, and the NSE public website endpoint is not a licensed real-time feed.

## Checks completed locally

| Check | Result |
|---|---|
| Python unittest suite | **PASS — 13/13** |
| Playwright/Chromium dashboard interaction smoke test | **PASS** |
| Mobile viewport horizontal-overflow test (390 px) | **PASS** |
| Factor-backtest input/metrics tests | **PASS — 6 tests** |
| Client/native engine version handshake regression | **PASS** |
| Unsafe news URL scheme regression | **PASS** |
| Inline JavaScript syntax | **PASS — 2/2 script blocks** |
| AndroidManifest XML parse | **PASS** |
| GitHub Actions workflow YAML parse | **PASS** |
| Literal frontend API route audit | **PASS — 23 frontend route literals, no missing native handler literals** |
| ZIP integrity | Checked after packaging; see final delivery summary |

## Not verified / remaining release gates

- **Android APK build and emulator/device launch:** NOT RUN locally. `gradle` and Android SDK are not installed/configured in this environment. The GitHub Actions workflow includes these checks, but it must actually run and pass.
- **Live NSE quote request:** NOT independently verified in this run. The public NSE website endpoint is best-effort, can be rate-limited/blocked or change schema, and is not a licensed real-time market-data feed.
- **Moneycontrol:** NOT integrated; no verified authorized feed/access configuration is present.
- **Historical OHLCV:** still uses third-party Yahoo Finance and is not NSE-verified.
- **Screener.in:** HTML parsing remains best-effort and subject to page changes/access terms; cookie detection alone does not establish that a protected request succeeded.
- **Upcoming results/corporate actions:** a verified embedded live calendar is not integrated; the app provides official source links rather than claiming a complete feed.
- **Trading strategy quality:** no genuine survivorship-aware, point-in-time out-of-sample strategy backtest was run. Synthetic unit tests validate the backtest utility, not trading profitability.
- **Security:** these are targeted source hardening changes, not a complete penetration test or independent security review.

## Release decision

**Status: Improved candidate build; NOT yet certified 10/10 or production-ready.** Before release, run the included GitHub Actions workflow successfully, install and test the resulting APK on target Android versions, verify provider data against source pages/authorized feeds, and complete the remaining calendar, data-quality and strategy-validation gates.
