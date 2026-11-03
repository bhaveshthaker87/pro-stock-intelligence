# PRO STOCK INTELLIGENCE V41.00 — NSE EOD full-universe search

## Release notes
- Android version: V41.00 / versionCode 88.
- Search suggestions now read the newest bundled official NSE CM-UDiFF EQ bhavcopy and search all symbols present in that report, rather than relying only on 28 hard-coded examples.
- Search results explicitly identify the NSE EOD report as the source and do not imply BSE coverage or live quotes.
- Peer comparison can show official NSE EOD closes and day changes for curated same-sector peers when their symbols exist in the bundled history; missing fundamentals remain blank until a dated Screener export or authorized source is supplied.
- Quotes remain unavailable unless an authorized HTTPS provider gateway is configured. NSE EOD close is not represented as a live quote.
- Screener fundamentals still require a valid user-authorized session or permitted CSV import; HTTP 401/403 is not bypassed.
- Exact index levels/history, automatic dividends/corporate actions, results calendar and embedded company news remain dependent on a validated authorized source or permitted dated import; official links are shown instead of fabricated rows.
- CI success proves build/tests/emulator checks only; it does not certify live-feed licensing, complete fundamentals, or investment performance.

