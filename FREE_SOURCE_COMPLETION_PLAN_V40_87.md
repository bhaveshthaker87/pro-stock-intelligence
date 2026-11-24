# V40.87 — Free-source integration plan and release acceptance

## Objective

Complete the no-new-paid-provider path for Pro Stock Intelligence while keeping source attribution, data freshness, exchange coverage and licensing explicit. This plan does not claim real-time NSE data, an unrestricted API, or redistribution permission.

## Repository baseline (2026-11-01)

- Main is V40.86 (versionCode 85).
- PR #31 bundles official NSE EOD history in the APK for the currently tracked 28 symbols; it is not a complete NSE/BSE universe.
- PR #29 adds a standalone manual Nifty index CSV importer and retains NSE corporate archive source files (An/Bc/Bm) as raw files. It does not normalize them or connect them to app UI.
- PR #33 adds peer and company-news CSV import; imported records are not an automatic/live news or peer service.
- Latest main CI run #686 passed debug build, tests, lint and emulator smoke. The live gateway and signed-release steps were skipped; do not report those as passed.

## Architecture decision

Use a source-adapter + canonical normalized store. Every record must carry:
- exchange/source/provider
- symbol/security identifier where applicable
- exchange event/trading date
- source publication timestamp and local fetch timestamp
- source URL and original-file SHA-256
- period, units, currency, standalone/consolidated basis for financial metrics
- marketDataStatus (EOD/DELAYED/REALTIME) and validation state
- correction/revision lineage where source supplies it

Never silently substitute EOD for live, another exchange's symbol, a stale event, or an unavailable financial metric.

## Workstream 1 — Official market data and indices (P1)

1. Build a complete NSE security-master importer from the official NSE CM MII security files exposed in the All Reports page. Preserve symbol, series, ISIN, security name, status and effective date. Include only eligible cash-equity series in the equity universe; retain other instruments as separate asset classes.
2. Add BSE's official security list as a separate exchange adapter. Do not infer BSE symbols by copying NSE symbols.
3. Extend the official NSE CM-UDiFF EOD ingestion to all eligible cash-equity rows, not only the 28 tracked names. Keep data partitions by exchange/trading date and compress historical files for APK/backend size control. Prefer download-on-demand/local cache over bundling the whole market history in the APK.
4. Add official NSE 52-week report, PE report and full bhavcopy/delivery data ingestion with date, unit, symbol and duplicate validation. Avoid calculating adjusted 52-week prices incorrectly: NSE notes adjusted columns reflect corporate actions.
5. Extend index importer to multiple NSE/Nifty indices using official historical-index CSV exports; retain index history separately from stock OHLCV. Provide a UI import/refresh path and source timestamp.
6. Explicitly exclude unauthorized live/intraday quote claims. Live index and quote values stay NOT CONFIGURED until an authorized endpoint has passed a freshness and entitlement test.

Acceptance:
- Security-master counts reconcile to the downloaded official file, with excluded series reported.
- At least 30 randomly selected securities are reconciled to official source rows.
- EOD OHLCV duplicates, invalid OHLC ranges, symbol/date mismatches and bad volumes fail closed.
- 52-week and PE reports show report date and exchange source.
- Empty or stale data cannot pass as fresh.

## Workstream 2 — Corporate actions, announcements, calendar and results (P1)

1. Use official NSE Corporate Filings Event Calendar CSV export as the primary structured event source. Its fields include symbol, company, purpose, details and date. Build a strict adapter and store exact source payload and source timestamp.
2. Use official NSE Corporate Filings Announcements export as the primary disclosure feed. Preserve subject, details, attachment URL, XBRL URL and broadcast date/time.
3. Parse NSE Market Activity ZIP categories An (announcements), Bc (corporate actions) and Bm (board meetings) only after collecting real official sample files and documenting stable schemas. Until schema tests exist, continue retaining raw source files and link the official page.
4. Add official corporate actions rows: event type, ex-date/record date, ratio/amount, symbol, source link. Distinguish proposed, approved, announced, revised and cancelled status when source data supports it.
5. Add financial results from official exchange financial-result filing exports/attachments. Parse statement tables with standalone/consolidated basis, quarter/half-year/year, units, audit status, filing timestamp and restatement/correction. Do not confuse a meeting date with a results publication date.
6. Add BSE official announcements/results/corporate-actions as a separately validated adapter and deduplicate cross-listed events by ISIN + event identity while preserving both exchange references.
7. Add stale-event rules: an upcoming event is expired after its scheduled date; changed/cancelled items update state; missing event coverage shows UNKNOWN/PARTIAL, never “no events”.

Acceptance:
- Fixture tests from at least 10 real sanitized NSE exports across event categories.
- Compare 30 symbols and date windows to the official calendar/announcements export.
- Every event detail opens its original official source.
- No fabricated dates, descriptions or absent-event claims.
- Record counts, missing rows, duplicate rows and parse failures are in the ingestion report.

## Workstream 3 — Fundamentals, peer maps and source imports (P1)

1. Keep Screener login as a user-operated official WebView. HTTP 403 stops retry; no cookie extraction, antibot bypass, credential sharing or direct hidden API.
2. Improve Screener Premium CSV/XLSX import: header aliases, decimal and Indian grouping, Cr/Lakh/absolute currency units, % values, negative parentheses, missing-value tokens, dates and fiscal periods. Keep raw input values alongside normalized values.
3. Require explicit financial basis (standalone/consolidated), unit, currency and reporting period for every metric. No cross-period or cross-basis calculation.
4. Build fundamentals from both user-exported Screener data and official NSE/BSE filing attachments. Mark each field's source and reporting period.
5. Create a maintained peer taxonomy using industry and sub-industry, with symbol/ISIN mapping and manual override. Candidates alone must not be displayed as verified peers.
6. Compare company and peers only on same metric definitions, units, basis and compatible periods. Show per-metric coverage; exclude missing values from rank denominator rather than scoring missing data as zero.
7. Add computed metrics with visible formulas and input provenance: PE, PB, ROE, ROCE, debt/equity, margins and growth only where inputs are available. For ROE use average equity where opening/closing equity exists. Clearly distinguish reported ratios from derived ratios.
8. Add a 30-stock reconciliation harness: symbol, data source, source URL/file hash, period, basis, units, source value, app value, variance, expected tolerance, pass/fail. Include banks/NBFCs, manufacturing, IT, pharma and other sectors; use sector-appropriate metrics.
9. Factor score must expose components, weights, coverage percentage and as-of date. A missing input lowers coverage, not silently improves quality. Keep scores descriptive unless point-in-time survivorship-aware backtest demonstrates predictive power.

Acceptance:
- At least 30 stocks reconciled against current official/Screener exports.
- Unit conversions and percent/Cr/Lakh edge cases covered by tests.
- Standalone and consolidated cannot be accidentally mixed.
- Peer sets are sector-compatible and each metric period is comparable.
- No “verified” label without an external reference reconciliation.

## Workstream 4 — Chart engine and indicators (P2)

1. Prototype TradingView Lightweight Charts 5.2.0 locally bundled in the Android WebView. Confirm license notice and include required attribution/notice. It is a renderer, not a price data provider.
2. Preserve existing app API/state model and replace only chart rendering behind an adapter. Avoid duplicate chart engines or remote CDN dependencies.
3. Create deterministic OHLCV fixtures covering gaps, splits/adjustments, weekends, flat prices and low volume.
4. Implement/validate SMA 20/50/200, RSI(14), Nadaraya-Watson Envelope and buy/sell markers separately from rendering. Signal rules and repainting behavior must be documented; use closed bars for confirmed signals.
5. Keep volume pane, crosshair OHLC/date, pan/zoom, responsive resize, landscape and fullscreen. Do not overlay price labels over candles; keep indicator panes distinct.
6. Validate every indicator against independently computed reference outputs to stated numeric tolerances.

Acceptance:
- Playwright browser checks and Android emulator checks.
- 20 deterministic chart fixtures; indicator parity report.
- Crosshair/zoom/resize/landscape/fullscreen and mobile-overflow tests.
- No signals when history is insufficient; missing/invalid candles produce explicit state.
- Library is bundled locally; app remains functional offline with imported history.

## Workstream 5 — Free RSS/news fallback

Use official exchange announcements as the primary disclosure feed. RSS/Atom is only a headline discovery layer if a publisher provides a permitted feed. Store publisher, title, published timestamp and HTTPS canonical URL; do not scrape paywalled article text or mirror full articles. Do not represent this as a complete/licensed financial news feed.

## Release gates

A release report must separately show:
- build/test/lint/emulator state
- signed APK state
- market quote freshness state
- EOD date and exchange/security coverage
- index date and covered index list
- events/results data window and parse coverage
- fundamentals import date, coverage and reconciliation
- peer coverage and matching periods
- chart indicator parity report
- licensing/redistribution status
- known limitations and failed tests

Debug CI success is not evidence of live data or signed production readiness.

## Execution order

1. Security masters + complete official EOD and index imports.
2. Official event-calendar/announcement CSV normalization and UI.
3. Corporate-actions and results adapters using real exports.
4. Screener/official-financial-statement normalization and 30-stock reconciliation.
5. Peer taxonomy and fair comparisons.
6. Lightweight Charts adapter and indicator parity tests.
7. Final emulator/device QA and release report.

All integrations must remain fail-closed, source-labelled and useful with no external gateway configured.
