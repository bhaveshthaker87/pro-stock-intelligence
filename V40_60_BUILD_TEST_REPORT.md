# Pro Stock Intelligence V40.60 — Source Upgrade & Build/Test Report

**Date:** 2026-10-11  
**Package version:** `40.60` (`versionCode 59`)  
**Status:** Quality-improved source candidate. **Not certified 10/10 or production-ready.**

## Fixes applied in this pass

1. **Corrected a misleading provider-confidence label.** The Screener enrichment path used to label mixed-source data `AUTHENTICATED`, despite price/history being sourced from other providers and freshness not being certified. It now explicitly says `SESSION-BASED / MIXED SOURCES — VERIFY PROVIDERS AND TIMESTAMPS` in both the native API and UI. The provider-status message now instructs users to verify quote source/timestamp.
2. **Corrected event-source wording.** Yahoo Finance dividend/split rows are described as third-party returned data that must be confirmed with the exchange, not simply “verified” events.
3. **Made the browser test portable across CI.** Playwright tests no longer hard-code `/usr/bin/chromium`; they use the browser installed by `playwright install`, avoiding a common GitHub Actions mismatch.
4. **Added pull-request validation.** The Android build/test workflow now runs for pull requests targeting `main`, not only pushes and manual dispatch.
5. **Added APK integrity evidence.** CI generates a SHA-256 checksum beside the debug APK and uploads both artifacts.
6. **Aligned release identity.** UI/native engine contract is `V40.60 PRO RELEASE HARDENING`; Android `versionName` is `40.60`, `versionCode` is `59`, and CI artifact names use V40-60.
7. **Removed an ambiguous “LIVE ENGINE” label.** The UI now labels the component `NATIVE ENGINE`, avoiding an implication that the market data feed itself is necessarily live.

## Validation results in this workspace

| Check | Result |
|---|---|
| `python -m pytest -q` | **PASS — 15 passed** |
| `python -m unittest discover -s tests -v` (same command used by CI) | **PASS — 15 tests** |
| Inline JavaScript syntax via Node `--check` | **PASS — 2/2 script blocks** |
| AndroidManifest XML parse | **PASS** |
| GitHub Actions workflow YAML parse | **PASS** |
| UI/native version contract and artifact-version regressions | **PASS** |
| ZIP CRC/integrity and SHA-256 | Checked after packaging; see `FINAL_V40_60_BUILD_TEST_SUMMARY.md` |
| Local Android Gradle build / emulator | **NOT RUN** — Gradle, Android SDK and ADB are unavailable in this environment |

## Remaining release blockers — not safely fixable by relabeling

- **Licensed real-time market data:** no authorized, configured exchange/vendor feed is present. The public NSE website endpoint is best-effort and not a licensed real-time feed; Yahoo Finance remains third-party history/quote fallback. Provider responses and timestamps need live validation.
- **Moneycontrol:** not integrated; no verified authorized feed/configuration was supplied.
- **Screener.in:** parsing remains dependent on its website/session behavior. Session detection does not guarantee that every requested field/query was accepted, fresh, or complete.
- **Upcoming results/corporate actions:** a verified live calendar feed is not integrated. The app intentionally shows official links and no fabricated dates.
- **Factor strategy evidence:** the backtest utility requires real point-in-time score snapshots, subsequent returns, a survivorship-aware universe, and realistic costs. No genuine out-of-sample result is claimed.
- **Android execution:** the local environment lacks the Android SDK/Gradle/ADB runtime required for a local APK build and emulator launch. CI must actually complete successfully; the workflow definition itself is not proof of a successful APK.
- **Security and maintainability:** this pass is not an independent penetration test or a full refactor of the monolithic Kotlin/HTML implementation.

## Release decision

V40.60 is a stronger and more honest source candidate with regression coverage for the fixes above. It must not be called 10/10 until live provider correctness, an authorized calendar/feed, Android CI build + emulator/device execution, and real out-of-sample validation are demonstrated.
