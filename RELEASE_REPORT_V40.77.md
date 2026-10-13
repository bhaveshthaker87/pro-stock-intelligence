# V40.77 implementation and verification notes

## Implemented in this branch
- Adds best-effort 60-second intraday chart/quote refresh only while the 1D range is selected and the app page is visible.
- Avoids overlapping refreshes and ignores a quote response if the user changed the selected symbol while it was in flight.
- Preserves the user's visible candle count when the 1D chart refreshes, keeping the newest candles in view.
- Makes price/volume chart plot margins responsive on narrow mobile canvases.
- Updates app, native engine, tests and artifact naming to V40.77 (versionCode 76).

## Important data-provider limitation
This change does not manufacture a real-time feed. The existing chart source is Yahoo Finance chart history and the app intentionally marks it as not certified exchange-live. The repository's provider contract states that no licensed market-data vendor is configured. A licensed/authorized provider contract and server-side gateway configuration are required before claiming exchange-real-time data. Screener session success must be tested with a real signed-in user session; CI cannot validate a user's private account.

## Verification status
CI results will be linked after the workflow completes. A passing build and deterministic tests do not, by themselves, prove live account data or exchange-real-time latency.
