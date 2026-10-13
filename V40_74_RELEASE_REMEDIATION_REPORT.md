# Pro Stock Intelligence V40.74 — Chart Data Integrity Remediation

Date: 2026-10-11  
Base: V40.73 source candidate  
Release status: **improved source candidate; not production-certified and not rated 10/10**.

## Issues fixed in this iteration

1. **Timestamp normalization:** chart bars can arrive with epoch seconds, epoch milliseconds, or ISO dates. Normalize valid times to epoch milliseconds so the UI does not silently interpret epoch seconds as dates in 1970.
2. **Chronological ordering:** sort bars by normalized timestamp before indicators and chart drawing.
3. **Duplicate candles:** deterministically retain the last input record for a duplicate timestamp, avoiding double-counted observations in RSI/SMA/NW calculations.
4. **Invalid OHLC rejection:** reject bars where high cannot contain open/close, low cannot contain open/close, OHLC prices are non-positive, or volume is negative. This prevents invalid candles from distorting chart scales and signals.
5. **Flat-market RSI edge case:** when both average gains and losses are zero, RSI is neutral 50 rather than incorrectly reporting 100 (overbought). All-gain and all-loss windows remain 100 and 0 respectively.
6. **Regression coverage:** added four behavior-level Node.js tests that execute the actual `cleanRows` function shipped in the UI: time normalization/sorting/deduplication, invalid OHLC/volume rejection, flat-market RSI, and ISO timestamp conversion.
7. **Version contract:** updated UI/native version handshake, Android `versionCode 73` / `versionName 40.74`, and CI artifact labels.

## Verification results

- Full pytest suite: **76 passed**.
- Python test/source compilation: PASS.
- Android manifest XML parse: PASS.
- Inline JavaScript syntax: 2 non-empty inline blocks PASS.
- CSV importer JavaScript syntax: PASS.
- ZIP integrity: checked after packaging.
- Actual live Screener session probe: **not run** (no user session/credentials supplied to this execution).
- Moneycontrol automated feed: **not implemented**; the official terms restrict automated extraction and machine-readable database use without prior express written permission. Public page viewing is not equivalent to an authorized feed. See [Moneycontrol terms](https://www.moneycontrol.com/cdata/termsofuse.php).
- Screener API: official support says Screener does not provide APIs and documents CSV export for Premium users. See [Screener CSV export guide](https://support.screener.in/article/28/export-screen-results).
- Android Gradle build, Android Lint, signed APK, emulator/device QA, APK security scan: **not run** because Gradle/Android SDK/ADB are unavailable in this environment.
- Independent 30-stock fundamental reconciliation and golden OHLCV indicator parity: **not completed**. These require comparable licensed/source-attributed datasets and reference results; fabricated fixtures cannot substitute for evidence.

## Updated ratings (evidence-based)

| Area | V40.73 | V40.74 | Reason |
|---|---:|---:|---|
| Source regression safety | 8.0 | 8.2 | Added executable chart-normalization regressions |
| Screener diagnostics/parser validation | 7.0 | 7.0 | No live account probe in this run |
| Fundamental accuracy evidence across stocks | 4.5 | 4.5 | 30-stock independent reconciliation still absent |
| Moneycontrol automated integration | 0.0 | 0.0 | Deliberately disabled pending authorized feed/permission |
| Chart/indicator reference verification | 6.0 | 7.2 | Invalid bars, time ordering and flat RSI fixed; no golden parity report yet |
| Android release confidence | 3.5 | 3.5 | Build/lint/APK/device tests not run |
| **Overall release readiness** | **6.6** | **6.8/10** | Better chart input integrity, but core live-data and Android release evidence still missing |

## What is still required before a credible 10/10 rating

- Run a real Screener session validation and capture sanitized, timestamped output.
- Compare at least 30 stocks field-by-field with source, period, units, consolidated/standalone basis and timestamp recorded.
- Verify RSI(14), SMA50/SMA200 and Nadaraya–Watson values against a known OHLCV golden dataset, including corporate-action-adjusted/unadjusted series behavior.
- Configure a licensed quote/fundamental/event feed or obtain explicit written authorization for any source integration that requires it. Do not bypass source terms.
- Build APK, run Android Lint, install on emulator and physical device, inspect logs, run security/dependency checks, and archive reproducible CI evidence.

A 10/10 label is intentionally withheld. The code fixes above are implemented and locally tested; the unverified items are genuine release gates, not claims that can be solved by changing a score.
