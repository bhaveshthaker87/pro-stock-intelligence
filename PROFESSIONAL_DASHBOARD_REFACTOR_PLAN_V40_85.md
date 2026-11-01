# Professional Dashboard Refactor Plan — V40.85

## Product decision

Build a trustworthy research workspace, not a screen that fills every blank with estimates. Separate source connectivity, field coverage, freshness, and calculated indicators. A successful login or page request must never imply complete fundamentals.

## Three implementation paths

### A — Authorized data gateway (preferred for recurring automation)
- One HTTPS server-side gateway for licensed quote, fundamentals, peer, event and news feeds.
- Keep vendor credentials server-side; validate schema, symbol, period, currency/unit, source timestamp and staleness.
- Best option for stable refresh and full peer/news/event automation.
- Requires a data agreement/provider subscription and gateway credentials; no such credentials are currently configured.

### B — Official NSE public data + Screener export (current no-new-provider path)
- Use NSE public EOD bhavcopy/history for OHLCV and official filings pages for verification.
- Use a user-exported Screener CSV/XLSX for fundamentals, ownership and quarterly statements.
- Store source, report period, retrieval time and original file fingerprint; show imported snapshots as snapshots, not live data.
- Public web pages/endpoints may change or rate-limit; this is not an SLA-backed real-time feed.

### C — Manual research links only (fallback)
- Open official NSE/Screener pages from each stock's detail view.
- Do not display a false empty calendar as “no upcoming events”.
- Lowest automation, highest transparency.

## Delivery stages

1. **P0 — Trust and usability:** truthful Screener status, clear login/import flow, separate source and freshness badges, missing-metric summary, fix Android status-bar overlap, declutter mobile chart.
2. **P1 — Data coverage:** robust Screener workbook ingestion for ratios, annual/quarterly results and ownership; validate units and periods; create a 30-stock reconciliation report.
3. **P1 — Events and news:** parse official NSE corporate filings / board meeting / results records only where fields and timestamps are validated; otherwise show official source links and an explicit unavailable state.
4. **P1 — Peer comparison:** sector taxonomy + curated peer universe; fetch same-period Screener metrics for each peer; show coverage and exclude incomplete peers rather than inventing values.
5. **P2 — Chart workspace:** independent price/volume/RSI panes, responsive candle spacing, one recent signal marker at a time, no overprinted text, proper pan/zoom/crosshair and fullscreen; validate indicators against deterministic fixtures.
6. **Release gate:** unit/UI tests, Android lint, emulator screenshot inspection, 30-stock data reconciliation, then physical-device acceptance. Signed release additionally requires the user's keystore secrets.

## Current implementation in this change
- Renames the Screener button to a clear login/action label and replaces “Session Verified” with “Page Access OK”; it explicitly states that page access does not certify every field or freshness.
- Moves missing ratio metrics into a compact expandable list, preserving the distinction between unavailable and zero.
- Reduces chart height on mobile, removes repeated BUY/SELL text labels, displays only the latest signal marker in the visible range, and removes colliding canvas OHLC/volume text.
- Applies Android system-bar insets and matching bar colors to prevent the app header overlapping status icons.

## Hard blockers / not claimed as solved
- Screener HTTP 403 cannot be bypassed; use official login and permitted exports if access remains denied.
- No authorized live quote/index gateway is configured. NSE EOD is historical, not intraday.
- Automated events/news/peer coverage remains incomplete until an approved source is available and validated.
- Missing metrics remain missing until a genuine source value or a defensible, labelled calculation exists.
