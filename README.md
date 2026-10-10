# PRO STOCK INTELLIGENCE V40.53 — deep UI and data-integrity testing

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
