# Pro Stock Intelligence V40.63 — Security and Release Hardening Report

**Date:** 2026-10-11  
**Version:** `40.63` / Android `versionCode 62`  
**Status:** Improved security candidate; not production-certified.

## Changes in V40.63

1. **WebView navigation allowlist:** only the app asset origin and `screener.in` HTTPS domain remain inside the WebView. Other HTTPS destinations open in the external browser. HTTP, `javascript:`, `file:`, `content:`, and other non-HTTPS schemes are blocked from navigation.
2. **Reduced cookie exposure:** disabled third-party cookies while retaining first-party Screener login.
3. **Backup and transport hardening:** Android backup is disabled; cleartext traffic remains disabled.
4. **Runtime diagnostics:** JavaScript console errors are logged under `PSI_WEB`; emulator CI checks Android runtime and uncaught JavaScript errors.
5. **CI evidence:** added Android lint and an artifact upload for its HTML report. Existing APK build, emulator launch, foreground process, screenshot, crash-log and checksum steps remain.
6. **Release consistency:** frontend/native version handshake, Android `versionName` `40.63`, Android `versionCode` `62`, tests, and workflow artifact names are aligned.

## Local verification executed

| Check | Result |
|---|---|
| `python -m pytest -q` | **PASS — 36 passed** |
| `python -m unittest discover -s tests -q` | **PASS — 36 passed** |
| Python compilation | **PASS** |
| Inline JavaScript syntax via `node --check` | **PASS — 2 inline script blocks extracted and checked** |
| Android manifest XML parse | **PASS** |
| CI workflow YAML parse | **PASS** |
| ZIP integrity | **PASS — checked during packaging** |
| Android Gradle build / lint / APK install / emulator launch | **NOT RUN locally** — no Gradle executable, Android SDK or ADB installed; outbound network/DNS unavailable for installing them |
| Remote GitHub Actions execution | **NOT VERIFIED FOR V40.63** — a separate older GitHub `main` commit (README V40.53 / Gradle V40.52) built successfully in Actions run #27, but that workflow only built/uploaded an APK and did not run V40.63 tests, lint, or emulator checks. See `PRODUCTION_RELEASE_EVIDENCE_2026-10-11.md`. |

## Remaining production blockers (not solvable by source-only edits)

### Market-data authorization and factual validation
The app still uses best-effort NSE public website and Yahoo Finance paths for quote/history and does not have an authorized vendor account or deployed, authenticated server-side gateway configured. Moneycontrol remains unintegrated. A data schema validator cannot certify source truth, exchange timing, licensing, or distribution rights. NSE describes authorized real-time data and data-use agreements at:
- https://www.nseindia.com/static/market-data/real-time-data-subscription
- https://www.nseindia.com/static/market-data/nse-data-policy

### Corporate event coverage
The app does not yet embed a verified official calendar for results, board meetings, dividends, splits, bonuses, rights and other events. It correctly avoids treating an empty third-party response as proof that no event exists. A supported data feed and valid credentials/subscription are required to close this gate.

### Trading performance
The backtest tool is exploratory and enforces some timestamp/holdout guards, but no real point-in-time score history, survivorship-aware universe including delisted names, verified corporate-action-adjusted returns, or broker-calibrated all-in transaction-cost dataset was provided. No strategy profitability claim is justified.

### Release runtime and security assurance
The workflow now attempts a full Gradle build, Android lint, emulator install/launch, screenshot capture, and runtime log inspection, but the workflow itself has not been run successfully in this environment. A successful CI run, signed release build, dependency/SBOM review, and independent security review are still needed.

## Rating

**Current source candidate: 7.5/10.** V40.63 improves app navigation isolation, cookie policy, backup posture, runtime diagnostics, and CI gates. A **10/10 production rating is not defensible yet** because market-data authorization/accuracy, corporate-event coverage, genuine out-of-sample strategy evidence, and Android runtime proof remain unverified. Do not mislabel this candidate as 10/10.
