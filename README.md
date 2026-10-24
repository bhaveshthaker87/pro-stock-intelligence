# PRO STOCK INTELLIGENCE V40.58 — professional release hardening

## V40.57 audit fixes
- Fixed missing-value coercion in AI/cockpit numeric parsing: null/empty values no longer become numeric zero and produce misleading technical states.
- Risk summary no longer describes missing risk data as “no major risk”; it shows explicit incomplete-coverage wording.
- Unified HTML, native provider, workflow artifact and Android app version to V40.57 / versionCode 55.
- Fixed Android SDK setup in GitHub Actions by explicitly installing platform-tools, Android 35 and build-tools 35.0.0.
- Updated the browser smoke test for version consistency and navigation between independent pages; all 8 local unit/UI tests pass. Inline JavaScript syntax and Android manifest XML validate.
- The APK has not been built in this environment; the GitHub Actions build and emulator test remain required.

## Changes in V40.47
- Fundamental score receives derived technical metrics before it is rendered; missing fields remain missing and do not count as passes.
- Fundamental parser now attempts to derive latest net profit, operating margin, sales/profit/EPS CAGR, current ratio and interest coverage from available Screener tables. These are best-effort HTML parses and must be reconciled against the provider page.
- 1D chart requests 5-minute candles and 1W requests 30-minute candles; longer ranges use daily bars. Yahoo-supported range aliases are normalized.
- Quote UI says third-party provider data may be delayed and shows the provider timestamp when Yahoo supplies it.
- The index ribbon no longer renders 15 empty placeholders as if they were populated; it shows actual returned indices plus a provider-coverage note.
- Annual table and shareholding calculations use the latest column in descending Screener table order; CAGR is calculated across the latest three annual intervals only.
- Screener status now distinguishes a detected cookie from a server-validated login; protected requests remain the definitive test.
- Dividend candidate screen uses an authenticated Screener query. It is first-page only.
- Peer lists are labelled candidates, not validated live comparisons.
- Upcoming earnings and future corporate actions are explicitly reported unavailable until an official calendar source is connected. No dates are fabricated.
- Cleartext HTTP disabled in Android manifest; version 40.47 / versionCode 47.

## Important limitations
- Yahoo Finance chart/search endpoints are third-party and undocumented; provider data may be delayed, blocked, rate-limited or changed.
- Technical scanners apply RSI(14) ≤ 30 and latest daily-bar change ≤ -5% filters over the app's tracked 28-symbol universe. Daily-bar data can be delayed or partial during market hours; these are not whole-market or intraday scans.
- Screener HTML scraping can break after page markup changes and should be used only in accordance with current Screener terms.
- Technical/fundamental scores are descriptive filters, not validated investment forecasts. The model has not been backtested.
- A full Gradle/APK build and real Android-device login/visual test must pass before release; this workspace does not have Android SDK/Gradle configured.


## V40.48 release-quality changes
- UI language no longer calls populated values “verified” unless they have not been independently validated; provider data and timestamps must be checked.
- Overall score is labeled as a rule-based screen, not a validated return forecast; the interface states that thresholds are not sector-adjusted.
- Removed decorative five-star rating that could imply a rating independent of the actual score.
- VersionCode 48 / versionName 40.48.

## Release gate status
This source package has static checks only. Do not rate it 10/10 or call it production-ready until an Android Gradle build, install/device tests, live-provider tests, complete calendar source integration, genuine RSI/drawdown filtering, peer-metric completeness, and historical out-of-sample backtesting have passed.


## V40.50 quality gates
- VersionCode 50 / versionName 40.50.
- GitHub Actions validates AndroidManifest.xml and checks every inline JavaScript block with Node before Gradle build.
- APK artifact name is version-aligned.
- This is not a claim that market data is exchange-certified or that every screen has been backtested.

## Known limitations that must remain visible
- Yahoo Finance is a third-party source; quote freshness and delay are not guaranteed.
- RSI oversold and daily crash scanners cover only the app's tracked 28-symbol universe. They use third-party daily data and do not represent a whole-market or intraday scan.
- Future corporate-action/result calendar and complete live peer metrics are not guaranteed in standalone mode.
- Screener query parsing returns the first available table and may be partial; verify terms and use authorized access.
- No APK/device run or historical-strategy backtest is certified by this source-only validation.


## V40.50 technical scanner scope
- The RSI Oversold scanner calculates a 14-session RSI from daily closes for the app's tracked 28-symbol universe and returns only RSI <= 30 matches.
- The Daily Crash scanner returns tracked symbols whose latest daily close is at least 5% below the previous daily close. It is not an intraday detector.
- Both scans use Yahoo Finance third-party chart data, can be delayed or unavailable, and are not a whole-market scan. Output includes checked-symbol coverage and does not claim complete coverage when requests time out.
- Upcoming corporate actions/results calendars remain unavailable until a reliable authorized source is integrated. Static checks are not a substitute for a full Android build and device test.


## V40.53 deep-test and data-integrity changes
- VersionCode 52 / versionName 40.52.
- Added a GitHub Actions Android Emulator smoke test that builds, installs, launches the APK and captures AndroidRuntime/Chromium errors. This is executed only when the workflow is run in GitHub Actions; it has not been run in this local workspace.
- Peer comparison now attempts live price history plus Screener fundamentals for each curated candidate, suppresses candidates with fewer than two available core fundamental fields, and reports partial coverage. This is a data-completeness check, not proof that peer classifications are exchange-certified or sector-identical.
- The corporate-actions and results cards now link directly to the official NSE event calendar and financial-results filings. NSE's official pages are dynamic; this standalone build does not scrape them or claim a complete live feed. Calendar dates remain blank rather than fabricated. See [NSE Event Calendar](https://www.nseindia.com/companies-listing/corporate-filings-event-calendar) and [NSE Financial Results](https://www.nseindia.com/companies-listing/corporate-filings-financial-results).
- Added `tools/factor_score_backtest.py`, a point-in-time backtest harness for historical factor-score snapshots and subsequent-period returns, plus automated unit tests. It intentionally refuses to generate performance results from today's factor scores; a real backtest requires historical as-of scores, forward returns, a survivorship-aware universe and cost assumptions.
- Locally passed: eight automated tests (six backtest validation tests plus two Playwright UI tests), including all six main tabs, core chart controls, saved scan execution, watchlist modal, alert creation/blank-alert rejection, malicious suggestion escaping, and a mobile-width overflow check. JavaScript syntax checks (2/2 inline blocks) and Android manifest XML parsing also pass.
- Not locally executed: full Gradle APK build, emulator/device install, live provider checks, or a genuine historical factor-score performance run. This environment has no Gradle executable, Android SDK, ADB or emulator and cannot resolve external hosts.


## V40.53 additional fixes and test coverage
- Corrected the frontend/server version handshake so the header no longer reports a stale V40.46 engine mismatch.
- Added the previously missing watchlist/alerts modal markup; the Watchlist and Alerts actions no longer dereference absent elements.
- Removed decorative chart toolbar controls that had no implementation and replaced them with a working expand/restore control (Escape also restores the chart).
- Hardened live search suggestion rendering against provider-controlled HTML injection.
- Fixed blank alert values being interpreted as zero and missing quote prices being interpreted as ₹0.
- Nadaraya–Watson BUY/SELL markers now require a closed-bar crossing back inside the envelope; wick touches alone no longer generate repeated markers. The same signals are attached to rows for alert evaluation.
- Peer metrics now request daily history long enough to calculate 50/200 DMA and Wilder-style RSI(14), where enough data is available. Market capitalization is displayed in ₹ Cr units, matching the column label.
- Backtest input now rejects factor scores outside 0–10; turnover uses portfolio replacement fraction instead of Jaccard distance, correcting transaction-cost calculations.
- Added Playwright UI smoke tests to GitHub Actions. The workflow has not yet run in this workspace; full Android Gradle build and emulator launch remain unverified until GitHub Actions completes successfully.
- Technical scanners now use Wilder RSI(14), matching the chart implementation; their status text notes that the latest daily bar may be partial during market hours.


## V40.57 consistency audit
- Corrected AI summary language so a low factor score is not automatically labelled a risk-heavy setup when verified risk flags are absent.
- Incomplete risk coverage now remains neutral and explicitly says that missing risk fields do not establish low risk.
- Added a clear third-party quote data disclaimer in the native provider payload.
- Added regression checks for risk-summary consistency and the market-data disclaimer.
- Live quote accuracy, Screener field-by-field validation, upcoming event feed integration, and a real Android APK/device test still require external verification.


## V40.57 source-transparency audit (2026-10-11)
- Android package version aligned to `versionName 40.57` / `versionCode 56`.
- Quote lookup now attempts the public NSE equity quote endpoint first. This is best-effort website access, **not a licensed real-time feed**, and may be blocked/rate-limited or change schema.
- Historical OHLCV bars are still sourced from Yahoo Finance as a clearly labelled third-party history fallback; they are not represented as NSE-verified bars.
- Moneycontrol is **not integrated** in this build: no verified endpoint/feed or access credentials were supplied. It is not safe to claim this requirement is complete.
- Screener.in remains the fundamentals/query source; a detected browser session does not alone prove protected API access is valid.
- Upcoming NSE corporate events/results still show official links rather than a verified embedded live calendar.
- Automated source/UI tests do not certify provider availability, data accuracy, trading profitability, or APK/emulator success.
- Before production release, use an authorized exchange/vendor feed for live prices and historical OHLCV, and test with real provider responses.


## V40.58 professional release hardening (2026-10-11)
- Bumped app metadata consistently to `versionName 40.58` / `versionCode 57`.
- Fixed a confirmed frontend/native version-handshake defect: the V40.57 UI expected a different engine string from the native `/api/health` endpoint, so the header could incorrectly warn of a version mismatch even when bundled files matched. Added a regression test requiring exact client/server engine contract equality.
- Added WebView Safe Browsing and disabled JavaScript-triggered popup windows. Added `onDestroy()` cleanup to stop loading and destroy the WebView lifecycle resource.
- Updated the GitHub Actions artifact names to V40.58; the workflow includes JavaScript syntax checks, Python/UI tests, Gradle APK build, and emulator launch smoke test. The workflow still must be executed successfully before treating the APK as verified.
- Preserved the source-provenance labels and explicit data limitations from V40.57.

### V40.58 verification status
- Python tests: run locally; see `V40_58_BUILD_TEST_REPORT.md`.
- Inline JavaScript syntax, Android manifest XML, ZIP integrity, and version handshake: checked locally.
- Android Gradle build/APK install: **not verified locally** (Gradle and Android SDK are not installed in this execution environment).
- NSE live quote endpoint: **not independently verified in this run**. Public NSE website endpoint access is best-effort, not a licensed real-time feed.
- Moneycontrol: **not integrated**. Historical OHLCV remains third-party Yahoo Finance.
- Upcoming results/corporate events: embedded live feed is **not integrated**; official source links are provided.
- This package is an improved candidate release, **not certified 10/10 or production-ready** until provider, build, device, security, and strategy validation gates are complete.

## V40.59 release-candidate audit (2026-10-11)
- Bumped current app metadata to `versionName 40.59` / `versionCode 58` so this package is distinct from the V40.58 candidate.
- Fixed stale GitHub Actions artifact names that still labelled the APK and emulator screenshot as V40-57 despite the V40.58 source version. Added a regression test to prevent workflow artifact/version drift.
- Re-ran the complete local automated test suite and packaging checks; see `V40_59_BUILD_TEST_REPORT.md`.
- This is a hardened release candidate, not a 10/10 certification. Android APK/emulator execution and live provider data remain external release gates.

## V40.60 quality hardening (2026-10-11)
- Advanced release metadata to `versionName 40.60` / `versionCode 59`.
- Replaced the overconfident `AUTHENTICATED` status for mixed-source Screener enrichment with explicit session/mixed-provider confidence wording; data freshness remains unverified.
- Reworded Yahoo Finance corporate-event results as third-party records that require exchange confirmation.
- Made Playwright Chromium launch portable for GitHub Actions, enabled pull-request CI, and added a SHA-256 checksum artifact for the APK.
- Changed the header badge from “LIVE ENGINE” to “NATIVE ENGINE” so it does not imply that market-data freshness is guaranteed.
- See `V40_60_BUILD_TEST_REPORT.md`. Live provider, official calendar, Android device, and out-of-sample strategy validation remain open release gates.

## V40.61 deep data-integrity hardening (2026-10-11)
- Advanced app metadata to `versionName 40.61` / `versionCode 60` and aligned the native health contract, UI tag, tests and CI artifacts.
- Corrected NSE public endpoint timestamp semantics: local response receipt is no longer reported as a provider quote timestamp.
- Replaced UI language that could imply licensed/live/verified data when freshness and authorization are not established.
- Corporate-event empty responses explicitly state that no returned events do not prove no events exist.
- Hardened API response cache/security headers and added source-label/timestamp regression tests.
- Added an optional `--oos-start` holdout window to the backtest utility, a configurable 25 bps default all-in turnover-cost assumption, and a small-sample warning.
- See `V40_61_DEEP_AUDIT_REPORT.md`. Authorized data feed, structured calendar, dataset-based strategy validation, and Android CI/device proof remain external release gates.

## V40.62 data-contract and release-gate hardening (2026-10-11)
- Advanced app metadata to `versionName 40.62` / `versionCode 61`; aligned UI/native health handshake and CI artifact names.
- Added `PROVIDER_GATEWAY.md`, a documented normalized schema for authorized quote/history/corporate-event feeds and explicit guidance to keep vendor secrets server-side.
- Added `tools/validate_provider_payloads.py` to reject stale/future/unzoned quotes, missing delay metadata, inconsistent or unordered OHLCV, and malformed corporate events. This validates provider payload shape/freshness claims; it does not establish licensing or factual accuracy.
- Tightened out-of-sample backtesting: `--oos-start` now requires `return_start_date` and `return_end_date` columns and rejects forward-return windows that start on/before the score as-of date. Results use `OUT_OF_SAMPLE_HOLDOUT_BOUNDARIES_VERIFIED` only after boundary checks pass.
- Strengthened emulator workflow assertions: verify the app is foregrounded and screenshot is non-empty; limit workflow token permissions to repository contents read.
- Automated validation: 34 tests pass, both inline JavaScript blocks parse, Android manifest XML parses, workflow YAML parses, and Python modules compile.
- Still not certified: no authorized market-data account/feed configured; no verified embedded corporate-event provider; no point-in-time survivorship-aware data supplied; no Android SDK/Gradle/ADB installed locally, and no remote CI run was triggered from this workspace. Do not interpret this candidate as a 10/10 production release until those external gates pass.

## V40.63 security hardening (2026-10-11)

- WebView navigation is restricted to the local app origin and Screener's own HTTPS domain. Other HTTPS links open in the external browser; non-HTTPS schemes are blocked.
- Third-party cookies are disabled for the WebView; first-party Screener login remains supported.
- Android app backup is disabled and cleartext traffic remains disabled.
- WebView JavaScript console errors are logged under `PSI_WEB` so emulator CI can fail on uncaught JavaScript errors.
- CI now runs Android lint and uploads its report, in addition to APK build and emulator launch checks.
- Automated local verification: 36 tests pass, JavaScript syntax and manifest checks pass.
- Important remaining release gates: no authorized live-data subscription/provider credentials, no verified embedded official corporate-event feed, no real point-in-time survivorship-aware dataset, and no successful Android CI run in this environment. Do not call the release production-certified until these are proven.


## V40.64 chart/source-provenance fixes

- Added a chart refresh control that refreshes the selected history and quote through the existing provider adapters, while retaining a visible warning that upstream freshness is not exchange-certified live.
- Added direct Screener company and Moneycontrol search links for the selected symbol. These are source links, not a claim that either provider's structured API is integrated.
- Corrected the `/api/screener-chart` route: it no longer silently returns Yahoo Finance history under a Screener chart endpoint name. It returns an explicit unsupported/documentation message.
- Chart status now shows provider, bar count and last-bar timestamp where available; it does not claim that historical bars are verified live.
- Added regression tests for chart controls and the Screener chart endpoint's source-provenance behavior.
- Updated version handshake and Android version to 40.64 / versionCode 63.

**External blockers remain:** Moneycontrol's published terms restrict automated extraction without prior express written permission; no public official API schema or credentials were supplied. Screener's public terms similarly do not establish permission for a third-party structured-data integration. See `PROVIDER_GATEWAY.md`. This release therefore uses explicit source links and does not falsely label data as Moneycontrol/Screener API data.


## V40.65 brand identity refresh
- Added a reusable vector brand mark (`brand-logo.svg`) for the in-app header and brand footer.
- Added a native Android launcher icon and referenced it from the application manifest.
- Updated UI/native engine version handshake, Android versionName to 40.65 and versionCode to 64, plus CI artifact labels.
- The supplied mockup is a visual target, not a claim that every screen has been rebuilt pixel-for-pixel. Existing dashboard functionality and data-source limitations remain unchanged.

## V40.81 release/data verification note

- GitHub Actions build success proves the project tests, Android compilation/lint and emulator smoke script passed for the specific commit; it does **not** prove the app has live market data.
- The authorized-provider gateway check now prints a visible **LIVE DATA NOT VERIFIED** warning and writes the status into the Actions job summary when `PROVIDER_GATEWAY_BASE_URL` is absent. For a release workflow that must reject missing live data, set repository variable `REQUIRE_LIVE_PROVIDER_GATEWAY=true`.
- To prove live data, configure a licensed/authorized HTTPS gateway and ensure quote, historical candles, events, dividends and indices payload checks pass. Secrets must remain server-side.
- Screener access uses the official login flow and must not bypass an HTTP 403. A detected browser cookie is not proof that protected company data can be fetched.
- The latest verified Actions run at review time is run #443 on PR #19 (not merged to `main`). It built V40.80 APK, lint report and emulator screenshot; the provider E2E step may have passed by skipping if the gateway URL was absent. Check its run summary for the explicit configuration notice before treating it as a live-data validation.
