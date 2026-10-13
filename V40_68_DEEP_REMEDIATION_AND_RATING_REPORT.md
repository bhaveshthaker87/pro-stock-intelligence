# Pro Stock Intelligence V40.68 — Deep Remediation and Release Rating

Date: 2026-10-11
Base: V40.68 expert-remediation source candidate
Status: **Improved source candidate; not production-certified**

## Changes made in V40.68

1. **Fundamental numeric parser hardening:** `asNumber` now rejects partial numeric matches (for example, malformed text containing a number), handles Unicode minus and parenthesized negatives, strips known display symbols/suffixes, rejects placeholders, and rejects non-finite values. The parser deliberately does not guess or convert unknown units; callers must supply field/unit semantics.
2. **Version alignment:** Updated source markers to V40.68 and Android versionName 40.68 / versionCode 67, including regression-test expectations. This is source-level alignment only; an APK has not been built from these changes, so runtime alignment still requires CI/build verification.
3. **Evidence honesty:** This report separates local regression results from checks that require live provider access, Android SDK/Gradle, CI, emulator, and devices.

## Validation run in this environment

- `pytest -q`: **50 passed** on the V40.68 Python test suite.
- `python3 -m py_compile tools/*.py tests/*.py`: passed.
- Android manifest XML parse: passed.
- Inline JavaScript syntax checks: passed for both extracted script blocks.
- ZIP integrity: checked after packaging.
- **Kotlin compile/build: NOT RUN** — Gradle and Android SDK are absent. The parser change is source-reviewed but not compiler-verified here.

## Requested issue-by-issue assessment

| Priority | Requirement | Current result | Evidence / remaining work |
|---|---|---|---|
| P0 | Fundamental parser and decimal/unit validation | **Partially remediated** | Strict parser change made. Kotlin compile and fixture-driven runtime tests remain required. Need representative Screener HTML fixtures covering PE, EPS, zero, decimals, comma grouping, negative values, missing values, and unit variants. |
| P0 | Independent verification of 30 stocks | **Blocked / not completed** | No fabricated comparison data is included. Requires same-cutoff-date data access and independent source records with source URL/provider, timestamp, period, unit, and discrepancy per metric. No live licensed feed configured. |
| P1 | Chart pipeline and indicator calculations | **Partially tested** | Existing suite passes and chart code has defensive recalculation for moving averages, RSI and Nadaraya–Watson envelope. A deterministic golden dataset test suite and independent calculation parity still need to run against the shipped WebView build. |
| P1 | Responsive chart workspace | **Not device-verified** | Source includes chart controls and resize-related logic; fullscreen, landscape, zoom, crosshair, resize and touch gestures need browser and Android emulator/device tests. |
| P1 | Provider resilience | **Partial** | Request timeouts exist. Retry/backoff, stale-cache age policy and explicit per-field stale/unavailable behaviour have not been proven end-to-end. Public website/Yahoo paths are not a licensed real-time feed. |
| P2 | Visual polish | **Source present; subjective QA pending** | Existing responsive dashboard and data cards remain. Needs visual regression screenshots at desktop/tablet/mobile widths and Android portrait/landscape, including loading/error/partial-data states. |
| P2 | Release hardening | **Partial** | 50 automated tests pass, manifest and JS checks pass. Gradle build, Android Lint, emulator/device run, APK secret/dependency scan, signed release and final checksum are not verified here. |

## Independent 30-stock report status

No stock values are asserted in this package as independently verified. A valid report must include 30 named stocks and, for each metric, source/provider, source URL or endpoint, capture timestamp, fiscal/quarter period, unit, app value, independent value, absolute/percentage difference, and pass/fail tolerance. The cutoff must be common across the dataset. A source mismatch or unavailable value must be marked unavailable, not filled by inference.

## Rating (evidence-based)

- **Source / automated regression quality: 7.2/10** — substantial functionality and 50 passing tests; parser hardening improved the source but its Kotlin compile is still unverified.
- **Data accuracy / independent validation: 4.5/10** — no completed 30-stock independent comparison and no configured licensed provider.
- **Release confidence: 5.0/10** — no local Android build, lint, emulator, real-device QA, signed APK or full security scan.
- **Overall evidence-based release rating: 6.0/10.** This is not an average claiming measured product quality; it is a conservative readiness rating weighted by the unverified P0/P1 requirements.

## Production release gates

1. Compile V40.68 with the configured Android Gradle Plugin/Gradle/JDK/SDK; fix all compiler and lint findings.
2. Add Kotlin unit tests against the actual parser and sanitized provider HTML fixtures; test decimals, locale grouping, negative/parenthesized values, blanks, malformed strings and unit boundaries.
3. Identify the authorized market-data provider, configure a server-side HTTPS gateway and secrets outside the APK, and run live smoke tests.
4. Complete the 30-stock common-cutoff independent comparison with metric-level provenance and tolerances.
5. Add deterministic OHLCV golden tests for RSI(14), SMA50/SMA200, Nadaraya–Watson envelope and buy/sell markers; compare against an independent reference implementation.
6. Verify timeout/retry/cache behaviour with simulated timeout, 429, 5xx, malformed JSON, stale data, future timestamps and wrong-symbol responses.
7. Run desktop/mobile browser QA and Android emulator/device QA, including fullscreen, landscape, zoom, crosshair, resize and touch.
8. Run CI build, Android Lint, dependency and APK secret scans, verify version alignment, generate checksums, and document signing/release provenance.

**Release decision: do not call this 10/10 or production-ready.** This package contains a concrete parser hardening change and an explicit verification report. It does not claim completion of live-data or device-dependent gates that could not be executed.

## Final package checks

- Updated V40.68 Python test suite: **50 passed**.
- Python compile check: **PASS**.
- Android manifest XML: **PASS**.
- Inline JavaScript syntax: **PASS (2 script blocks)**.
- Kotlin/Gradle build: **NOT RUN** (toolchain unavailable).
