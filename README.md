# PRO STOCK INTELLIGENCE V42.06 — NSE EOD full-universe search

## Release notes
- Android version: V42.06 candidate / versionCode 98 (release signing and production gates remain pending).
- Search suggestions now read the newest bundled official NSE CM-UDiFF EQ bhavcopy and search all symbols present in that report, rather than relying only on 28 hard-coded examples.
- Search results explicitly identify the NSE EOD report as the source and do not imply BSE coverage or live quotes.
- Peer comparison can show official NSE EOD closes and day changes for curated same-sector peers when their symbols exist in the bundled history; missing fundamentals remain blank until a dated Screener export or authorized source is supplied.
- Live/delayed quotes require the authorized NSE/vendor gateway or a timely validated official NSE MCP response. If those time out, the app now recovers the last validated official NSE EOD close and daily OHLCV history from the bundled NSE bhavcopy. EOD values are clearly labelled with their trading date and are never represented as live or intraday.
- Screener fundamentals require a valid user-authorized session. CSV/XLSX upload and imported-data fallbacks have been removed; HTTP 401/403 is not bypassed.
- Exact index levels/history, automatic dividends/corporate actions, results calendar and embedded company news remain dependent on a validated authorized source or permitted dated import; official links are shown instead of fabricated rows.
- CI success proves build/tests/emulator checks only; it does not certify live-feed licensing, complete fundamentals, or investment performance.

