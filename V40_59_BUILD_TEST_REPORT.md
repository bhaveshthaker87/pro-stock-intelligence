# Pro Stock Intelligence V40.59 — Build & Test Report

**Date:** 2026-10-11  
**Release candidate:** V40.59 / Android `versionCode 58`  
**Disposition:** Improved candidate; **not certified 10/10 or production-ready**.

## Source audit and fixes applied

1. **Release artifact version drift fixed.** The V40.58 workflow still uploaded APK and emulator screenshot artifacts with `V40-57` names. Updated the GitHub Actions artifact names to V40-59 and added a regression test that fails if V40-57 labels return.
2. **Release metadata advanced consistently.** Updated current HTML and native-engine labels to V40.59 and Android Gradle metadata to `versionName 40.59` / `versionCode 58`. The frontend/native health-engine handshake remains aligned.
3. **Preserved the existing feature set and safety/data limitations.** The existing dashboard, chart controls (including Nadaraya–Watson), watchlist, alerts, query cards, factor/backtest utilities, Screener-related features, risk coverage wording and provider caveats remain in the package.
4. **Retained prior V40.58 hardening.** WebView Safe Browsing, disabled JavaScript-opened popup windows, WebView lifecycle cleanup and unsafe news-link scheme blocking remain present.

## Checks run in this environment

| Check | Result |
|---|---|
| Python unit + Playwright/Chromium UI suite | **PASS — 14/14** |
| Main dashboard tabs, query execution, watchlist and alerts smoke test | **PASS** (deterministic mocked provider responses) |
| Mobile viewport horizontal-overflow test (390 px) | **PASS** |
| Frontend/native engine handshake regression | **PASS** |
| Workflow artifact version regression | **PASS** |
| Unsafe news URL scheme regression | **PASS** |
| Inline JavaScript syntax | **PASS — 2/2 script blocks via Node `--check`** |
| AndroidManifest XML parse | **PASS** |
| GitHub Actions workflow YAML parse | **PASS** |
| ZIP integrity / CRC | Checked after packaging; see final summary |

## Not verified — release gates still open

- **Android Gradle/APK build and emulator/device launch:** NOT RUN locally. `gradle`, Android SDK (`sdkmanager`) and `adb` are not installed in this environment. The GitHub Actions workflow is configured to build and run an emulator smoke test, but that workflow must actually run and pass.
- **Live NSE quote response:** NOT independently verified in this run. The public NSE website endpoint is best-effort, may be blocked/rate-limited or change schema, and is not a licensed real-time feed.
- **Moneycontrol:** NOT integrated; no verified authorized feed/access configuration is present.
- **Historical OHLCV:** sourced from third-party Yahoo Finance; it is not represented as NSE-verified history and freshness is not guaranteed.
- **Screener.in:** HTML/query parsing remains best-effort and may break with site changes or access controls. A detected cookie is not proof that a protected query succeeded.
- **Upcoming results/corporate actions:** a verified embedded live calendar is not integrated; official source links are provided instead of fabricated dates.
- **Trading performance:** no survivorship-aware, point-in-time, out-of-sample performance result was produced. Unit tests validate the backtest utility, not profitability.
- **Security:** targeted hardening only; no independent penetration test or complete security review was performed.

## Release decision

**V40.59 is an improved release candidate, not a 10/10 certification.** Release approval still requires a successful GitHub Actions build/emulator run, installation and visual testing on target Android devices, verification of live provider responses against authoritative/authorized sources, and closure of the data-quality/calendar/backtest/security gates above.
