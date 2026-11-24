# PRO STOCK INTELLIGENCE V42.07 — NSE EOD full-universe search

## Release notes
- Android version: V42.07 candidate / versionCode 99 (release signing and production gates remain pending).
- Search suggestions now read the newest bundled official NSE CM-UDiFF EQ bhavcopy and search all symbols present in that report, rather than relying only on 28 hard-coded examples.
- Search results explicitly identify the NSE EOD report as the source and do not imply BSE coverage or live quotes.
- Peer comparison can show official NSE EOD closes and day changes for curated same-sector peers when their symbols exist in the bundled history; missing fundamentals remain blank until a dated Screener export or authorized source is supplied.
- NSE MCP is disabled by default pending written permission for this app's intended use. No 1–3 minute delayed quote feed is claimed unless an authorized provider gateway is configured and its responses pass validation. Bundled NSE history is EOD only.
- Screener fundamentals require a valid user-authorized session. HTTP 401/403 is not bypassed. If company-page requests are blocked, the app accepts an official Screener CSV export as a clearly labelled, timestamped fundamentals fallback. It also exports a separate 30-stock app parser snapshot for the 540-field reconciliation.
- Exact index levels/history, automatic dividends/corporate actions, results calendar and embedded company news remain dependent on a validated authorized source or permitted dated import; official links are shown instead of fabricated rows.
- CI success proves build/tests/emulator checks only; it does not certify live-feed licensing, complete fundamentals, or investment performance.



## V42.07 zero-budget policy
- NSE MCP requests are disabled by default (`enableNseMcpData=false`) until written permission for the app's intended use is confirmed. Do not enable it merely because the public website is accessible.
- Screener.in remains the sole fundamentals source. No Yahoo Finance or Moneycontrol live quote fallback is used.
- When official bundled NSE EOD data is missing, the price remains unavailable. No price is fabricated or silently relabelled.
- See `docs/V42.07_ZERO_BUDGET_DATA_POLICY.md` for release gates and limitations.
