# Release Verification Plan — Pro Stock Intelligence V42.05

## Release rule
Do not merge or label a build release-ready unless every mandatory gate below has a recorded PASS. A skipped, mocked, unconfigured, stale, or unauthenticated check is NOT_TESTED, never PASS.

## Gate 1 — Static and regression validation
- Validate Android manifest XML and all inline JavaScript syntax.
- Run the complete Python unittest suite, including browser-based Playwright tests.
- Verify all nine navigation destinations: Overview, Charts, Financials, Ownership, Peers, News, Scans, Events, Data Sources.
- Verify active navigation state, query execution, watchlist persistence, alert validation, and chart controls.
- Preserve explicit regressions for quote/history row retention and NSE MCP request/response handling.

## Gate 2 — Android build and package integrity
- Build debug APK and run Android lint.
- Verify package ID, version code/name alignment, APK existence, and artifact naming.
- Install APK on the CI Android emulator, launch the foreground activity, and capture a screenshot.
- Treat build success without install/launch evidence as PARTIAL, not full PASS.

## Gate 3 — Official NSE provider smoke tests
- Exercise the official NSE CM Market MCP quote tool and official Bhavcopy history tool from the app's native runtime.
- Record HTTP status, MCP tool result status, symbol, source, timestamp, age, row count, and response schema.
- Verify quote values are labelled delayed and daily history is labelled EOD; never call either tick-live.
- Validate candle invariants (high/low/open/close), non-negative volume, chronological ordering, and no empty-array overwrite.
- Test timeout, HTTP error, malformed JSON/SSE, missing session ID, and stale response states.
- If NSE MCP is unavailable in CI, mark the external provider gate NOT_TESTED and do not infer success from source-code tests.

## Gate 4 — Screener authenticated session and fundamentals
- Test only with an explicitly configured, user-authorized Screener session; never bypass 403 or anti-bot controls.
- Require a successful authenticated company-page request (HTTP 200) before showing Connected.
- Verify parsed metrics carry source, observation timestamp, period, units, and provenance.
- Compare 30 stocks × 18 metrics (540 records) against Screener values with documented tolerances.
- Missing, blocked, or untested metrics remain NOT_TESTED; do not synthesize values or overwrite valid values with nulls.

## Gate 5 — Data honesty and source boundaries
- NSE is the only quote/history exchange feed in this build; Yahoo Finance and Moneycontrol are not live-price fallbacks.
- Do not label reference, cached, delayed, or EOD values as live.
- Index values, intraday candles, options/F&O, and corporate events must show explicit unavailable states unless a supported authorized source and timestamp are present.
- Provider outage must not erase previously validated history or leave stale charts presented as current.

## Gate 6 — Release readiness and security
- Keep provider credentials and tokens server-side; never place secrets in Android assets or logs.
- A signed production APK requires configured signing secrets, authorized provider gateway, and complete 540-record reconciliation evidence.
- Upload APK, emulator screenshot, test logs, and reconciliation report as workflow artifacts.
- Keep the PR open until all mandatory checks pass and limitations are recorded.

## Current execution notes
- Build #950 failed because the old smoke test asserted six tabs after the UI changed to nine sections. The assertion was replaced with explicit checks for all nine destinations, active state, and the Sources modal.
- The updated test change must be re-run by GitHub Actions before this plan can be marked complete.
- Previous CI diagnostics showed PROVIDER_GATEWAY_BASE_URL missing and Screener 30-stock reconciliation at 0/540 verified. These remain release blockers for live-provider/signing claims until reconfigured and re-tested.


## Latest implementation update
- Shared NSE quote resolver: configured authorized gateway, then official NSE delayed MCP, then bundled NSE EOD. Returned status and provider timestamp are retained; no Yahoo Finance or Moneycontrol fallback.
- Screener connection probe now requires at least 4 of 7 core fields (market cap, P/E, EPS, book value, ROE, ROCE, debt/equity). Low-coverage pages are explicitly flagged.
- The current 30 × 18 Screener audit is still source-side collection, not an app-vs-Screener comparison. The API now marks all 540 values as unreconciled until an independent app snapshot exists; it reports 0 verified comparisons rather than manufacturing a pass.
- Device login, actual chart/quote behavior, signed APK and checksum remain separate release gates.
