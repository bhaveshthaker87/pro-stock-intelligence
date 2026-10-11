# Pro Stock Intelligence V40.64 — Release Candidate Report

Date: 2026-10-11
Status: **tested local source candidate; not yet production-certified**

## Changes made

- Version handshake aligned across Android Gradle (`versionName 40.64`, `versionCode 63`), native `/api/health`, UI label, and CI artifact names.
- Added chart toolbar controls to refresh the available quote/history and open the selected symbol on Screener.in or Moneycontrol.
- Chart status now reports the provider, bar count, and last-bar timestamp where available, with an explicit warning that the series is **not certified exchange-live**.
- Removed false source attribution: `/api/screener-chart` previously returned the same Yahoo Finance history as `/api/history`. It now returns a clear unsupported response rather than pretending the response is Screener chart data.
- Added regression tests for the chart controls and source-attribution behavior.
- Preserved the WebView navigation allowlist, third-party-cookie restriction, no-cleartext setting, and disabled Android backup policy.

## Tests run locally

- `python -m pytest -q`: **38 passed**
- `python -m unittest discover -s tests -q`: **38 passed**
- `python3 -m py_compile tools/*.py tests/*.py`: passed
- Inline JavaScript extracted and checked with `node --check`: passed (2 inline script blocks)
- Android manifest XML parse: passed
- GitHub Actions workflow YAML parse: passed
- ZIP integrity check: passed after packaging

These are local source/UI tests. They do not certify provider accuracy or market-data freshness.

## Not verified in this environment

- Android Gradle build, Android lint, emulator install/launch and runtime log scan for this V40.64 source: not run locally because Gradle/Android SDK/emulator are not installed in the execution environment. The repository's previously observed successful Actions build belongs to an older `main` commit and is not evidence for V40.64.
- GitHub branch/PR creation: attempted and rejected by GitHub integration with HTTP 403 `Resource not accessible by integration`; no source was pushed to `main`.
- Live Moneycontrol API: not integrated. Moneycontrol's published Terms of Use restrict automated extraction and machine-readable reuse without prior express written permission. No official API/OpenAPI specification, approved endpoint contract, sanitized response, or credentials were supplied. The app opens Moneycontrol search as a source link only; this is not an API integration.
- Screener structured-data integration: existing code has a session-based parser for visible company pages and saved queries, but this is not a documented official API. The published terms do not establish authorization for a general third-party data service. The new toolbar opens the official company page; no undocumented Screener chart API is claimed.
- True real-time market data: current quote/history fallbacks include an NSE public website endpoint and Yahoo Finance history/quotes. They can be delayed, incomplete, rate-limited or changed. The UI now explicitly says that chart bars are not certified exchange-live. A permitted data feed and freshness SLA are still required.
- Corporate event coverage: no complete, authoritative, verified all-company calendar is embedded. Empty results mean no records were returned, not that no event exists.
- Strategy validity: no real point-in-time, survivorship-aware out-of-sample backtest using a historical universe including delisted stocks and adjusted returns has been proven by this release.
- Signed production APK, SBOM, external security review and end-to-end live-provider smoke test: not completed.

## Required next steps

1. Obtain written permission/API documentation from Moneycontrol and, if needed, Screener that covers structured access, display, history, caching and redistribution.
2. Deploy a server-side HTTPS gateway; store provider credentials only in server-side secrets. Do not place API secrets in Android, JavaScript, Gradle, or the APK.
3. Provide a sanitized vendor response fixture and validate quote/history/event schemas and timestamps.
4. Enable repository write access, push this candidate on a branch, and run the repository CI against the exact V40.64 commit. Verify APK, lint report, emulator screenshot, and runtime logs.
5. Validate a point-in-time backtest and official corporate-event feed before claiming production-grade data completeness.

## Rating

**Current defensible score: 7.8/10 for this local source candidate.** The chart provenance bug and refresh/source UX are improved and local tests pass. This is not a 10/10 production release because authorized live data, provider schema, event completeness, backtest evidence, and exact-commit Android runtime evidence remain outstanding.
