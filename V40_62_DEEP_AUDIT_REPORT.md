# Pro Stock Intelligence V40.62 — Deep Audit and Release-Gate Report

**Date:** 2026-10-11  
**Version:** `40.62` / Android `versionCode 61`  
**Status:** Data-contract and test hardening candidate; not production-certified.

## Source changes in this release

1. **Normalized provider contract:** added `PROVIDER_GATEWAY.md` documenting quote, OHLCV history, and corporate-event payloads; requires server-side secrets and explicit provider authorization. No undocumented vendor endpoint or credential has been invented.
2. **Provider payload validation:** added `tools/validate_provider_payloads.py`. Quote validation checks required source, timezone-aware `asOf`, positive finite price, declared realtime/delayed/EOD status, delay metadata, freshness windows and future timestamps. History validation checks chronology, duplicate timestamps, OHLC consistency, positive prices and nonnegative volume. Event validation checks event type, symbol, announcement timestamp and date. Empty event arrays never certify absence.
3. **Backtest look-ahead guard:** `--oos-start` now requires explicit `return_start_date` and `return_end_date` columns and validates that forward returns start strictly after each score's as-of date. The output mode says `OUT_OF_SAMPLE_HOLDOUT_BOUNDARIES_VERIFIED` only after this validation. This still cannot prove source timestamps, delisted-stock inclusion, corporate-action adjustment, or dataset correctness.
4. **Android CI checks:** workflow permissions limited to `contents: read`; emulator workflow waits for app start, asserts foreground activity, checks non-empty screenshot, and scans AndroidRuntime fatal exceptions.
5. **Release metadata:** UI badge, frontend/native version contract, Android `versionName 40.62`, `versionCode 61`, tests and artifact names aligned.

## Local verification

| Check | Result |
|---|---|
| `python -m pytest -q` | **PASS — 34 passed** |
| `python -m unittest discover -s tests -q` | **PASS — 34 passed** |
| Python bytecode compilation | **PASS** |
| Inline JavaScript syntax | **PASS — 2/2 script blocks** |
| Android manifest XML | **PASS** |
| GitHub Actions YAML parse | **PASS** |
| ZIP archive integrity | Checked during packaging |
| Android Gradle build / APK install / emulator | **NOT RUN** — Gradle and Android SDK/ADB are absent locally |
| Remote GitHub Actions result | **NOT RUN** — no repository connection/remote workflow execution was available |

## External release gates still open

### Authorized market data
The app does not have a licensed vendor account or deployed provider gateway configured. NSE's official documentation describes real-time feeds via direct subscription or authorized vendors and has separate data-use policy. See [NSE Real-Time Data](https://www.nseindia.com/static/market-data/real-time-data-subscription), [NSE Data Usage Policy](https://www.nseindia.com/static/market-data/nse-data-policy), and [NSE Corporate Data](https://www.nseindia.com/static/market-data/corporate-data-subscription). The new contract/validator prepares for integration but is **not** a live provider integration. Moneycontrol remains unintegrated.

### Corporate events/results
No verified structured event calendar is embedded. The existing app continues to direct users to official filings and does not fabricate dates. A supported feed, permitted usage, and real response samples are required.

### Trading-strategy evidence
No strategy-performance claim is made. A credible result needs point-in-time factor snapshots, forward-return windows, corporate-action handling, realistic brokerage/tax/slippage assumptions, and a survivorship-aware universe including delisted securities. The new validator reduces one leakage risk but does not generate the dataset.

### Android/runtime and security
Local environment has no `ANDROID_HOME`, `ANDROID_SDK_ROOT`, Gradle executable, or ADB. Workflow configuration is stronger, but no successful CI APK build, emulator/device launch, signed release build, SBOM/dependency audit, or independent penetration test has been demonstrated here.

## Rating

**Source candidate: 7.2/10.** Automated checks and validation gates improved, but live authorized data, an embedded event feed, a genuine dataset-based out-of-sample study, and actual Android build/runtime evidence remain unavailable. A 10/10 production rating is not defensible until these gates are closed with evidence.
