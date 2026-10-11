# Pro Stock Intelligence V40.70 — Screener data-quality hardening

Date: 2026-10-11  
Status: **Improved source candidate; not production-certified; no APK produced in this environment**

## Source changes

1. **Reject login/blocked/changed-markup pages.** Fundamental parsing now requires a company heading and the expected `top-ratios` section. Login responses and pages without those markers fail with an explicit error rather than returning an empty-looking “success”.
2. **Fail closed on ambiguous ratio labels.** A metric is accepted only when one unique, parseable value is found in the matching ratio list item. Positive-only fields (current price, market cap, book value, P/E) reject non-positive values. This reduces false positives; markup variants may be reported unavailable until a fixture-backed adapter is added.
3. **Fixed a time-period alignment defect in CAGR.** The prior `mapNotNull` logic could shift fiscal periods when a value was blank and compute a false 3-year CAGR. The revised logic preserves each fiscal column and only calculates when both the latest and exact three-period-back values are present and positive.
4. **Added fundamental provenance/quality metadata.** Screener payloads now include source URL, fetch timestamp, available/expected field counts, a coverage status and quality flags for key missing metrics.
5. **Aligned release markers.** UI/native engine version V40.70, Android versionName 40.70 / versionCode 69 and CI artifact names are aligned.

## Checks performed

- Python tests: **55 passed**.
- Python `py_compile`: **PASS**.
- Android manifest XML: **PASS**; inline JavaScript syntax (`node --check`): **PASS**; ZIP integrity: checked after packaging.
- Kotlin/Gradle build, Android Lint, emulator/device UI tests: **not run** (Gradle/Android SDK not available in this environment).
- Live Screener verification, 30-stock cross-check and authenticated-session integration: **not run**. The current runtime cannot establish a valid Screener session or prove that live page markup is stable.

## Important data-source limitation

Screener's official support documentation says it does not provide APIs and documents CSV export from its UI (export is a Premium feature). The app currently reads company HTML pages; that is not an official, versioned API contract. HTML can change, access can be gated, and no parser can guarantee all stocks without a stock-by-stock fixture suite and live verification. Do not describe this as “all stocks guaranteed accurate” or production 10/10.

Official reference: https://support.screener.in/article/28-export-screen-results
Terms: https://www.screener.in/guides/terms/

## Release rating

- Parser failure-mode safety: improved; static regression tests pass.
- Screener accuracy across all stocks: **not proven** (no live 30-stock comparison).
- Android build/release confidence: **not proven** (no Gradle build, lint, emulator or device run).
- Overall release readiness: **not 10/10** until live data verification, full build and device QA are complete.

## Next gates to reach a production release

1. Capture sanitized Screener HTML fixtures for large/mid/small caps, missing values, alternate labels, financials and shareholding; test parser behavior against them.
2. Run an independently checked 30-stock report at a common cutoff, preserving source URL, fetch time, fiscal/quarter period, unit and field-level differences.
3. Build the exact ZIP in Android CI; run Gradle tests/lint, emulator and Android portrait/landscape checks.
4. Test Screener login expiry, redirects, 403/429/5xx, timeout, wrong symbol and markup changes.
5. If reliable automated access is required at scale, obtain an authorized data export/feed or explicit provider permission rather than depending on undocumented HTML internals.
