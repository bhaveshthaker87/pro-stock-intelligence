# Pro Stock Intelligence V40.69 — Strict Fundamentals Remediation

Date: 2026-10-11  
Status: **Updated source candidate; not production-certified; no APK produced in this environment**

## Changes in this candidate

1. **Removed unsafe fundamental fallback.** Screener PE/EPS/ratio parsing no longer searches arbitrary visible text for the next nearby number after a label. That heuristic could silently attach a nearby but unrelated number to a financial metric. If a known metric DOM node cannot be parsed, the field remains unavailable rather than fabricated. This is intentionally conservative; markup variants may now show missing data until a specific, fixture-backed adapter is added.
2. **Strict numeric parsing retained.** Rejects malformed numeric fragments and non-finite values; handles Unicode minus and parenthesized negatives; does not guess unknown unit conversions.
3. **Version alignment.** Frontend, native health contract, Android `versionName` 40.69 / `versionCode` 68, and CI artifact labels updated.
4. **Regression coverage added.** New tests enforce fail-closed parsing and current release-version consistency.

## Local checks actually run

- Python test suite: **52 passed**.
- Python source compilation (`py_compile`): **PASS**.
- Android manifest XML parse: **PASS**.
- Both inline JavaScript blocks checked with Node.js `--check`: **PASS**.
- ZIP integrity: checked after packaging.
- Kotlin/Gradle build and Android Lint: **NOT RUN**; Gradle and Android SDK are unavailable in this environment.
- Emulator/device interaction and screenshots: **NOT RUN**.
- Live provider verification: **NOT RUN**.

## Seven requested areas

| Area | V40.69 result | Remaining evidence required |
|---|---|---|
| P0 parser and units | Unsafe nearby-number fallback removed; strict parsing retained | Kotlin compile + sanitized real Screener HTML fixtures across PE/EPS/decimal/locale/unit cases |
| P0 30-stock verification | Not completed; no values fabricated | Common-cutoff report with two independent sources, timestamps, periods, units, metric deltas and tolerances for 30 stocks |
| P1 chart calculations | Existing tests retained | Golden OHLCV vectors and independent RSI/SMA/Nadaraya–Watson reference parity on the shipped build |
| P1 responsive chart | Not device-verified | Browser and Android tests for fullscreen, landscape, zoom, crosshair, resize and touch |
| P1 provider resilience | Existing finite request timeouts; no new end-to-end resilience claim | Controlled 429/5xx/timeout/malformed/stale/wrong-symbol tests; retry/backoff/cache-age policy proof |
| P2 visual polish | Existing UI retained; release markers aligned | Screenshot regression at desktop/tablet/mobile and Android portrait/landscape including error/loading states |
| P2 release hardening | 52 tests and static checks pass; version markers aligned | CI Gradle build, lint, emulator run, dependency/security scan, signed release APK and checksum |

## Rating

- Source regression quality: **7.5/10** for the tested source paths.
- Fundamental-data accuracy: **4.5/10** pending independent 30-stock verification and provider fixtures.
- Release confidence: **5/10** pending Gradle build, lint, emulator and device evidence.
- Overall release readiness: **6.2/10**. This is not a claim that all seven areas are fixed or that the app is 10/10.

## Release decision

V40.69 is a safer source candidate because it removes a specific silent-misclassification path. It is not a finished production release. Live financial-data accuracy cannot be honestly certified without an authorized data provider and independent comparison evidence. Android release readiness cannot be certified until CI successfully builds and tests the exact ZIP.
