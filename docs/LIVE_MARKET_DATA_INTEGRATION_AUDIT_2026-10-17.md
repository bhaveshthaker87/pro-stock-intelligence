# Live market data integration audit — 2026-10-17

## Findings
- The Android client currently requests NSE public website quote data, but that is best-effort website access and does not establish an authorized real-time market-data license.
- Historical OHLCV bars and several technical scans currently call the Yahoo Finance chart endpoint. This conflicts with the product requirement to use only NSE, Screener.in, and Moneycontrol.
- Screener.in is currently parsed through website/session behavior; a signed-in session is not a documented general-purpose API contract.
- Moneycontrol is not integrated as a structured quote provider. Do not scrape it or infer undocumented endpoints without written permission or a supported feed contract.
- The uploaded TCS.xlsx is a Screener Excel customization workbook. Its Data Sheet contains TCS company metadata and a displayed Current Price of ₹2,465; this is a workbook snapshot, not a verified live quote or API response. Financial statements are on separate sheets.
- No authorized live NSE quote/index feed credentials, historical candle feed contract, or deployed server-side gateway were provided in the repository.

## Required architecture
1. Use an authorized NSE real-time vendor/feed for equity quotes and the required index segments; validate timestamps and entitlement.
2. Use an authorized historical OHLCV feed for charts/indicators. A quote feed does not automatically include candles.
3. Use Screener.in only through an explicitly permitted access method for fundamentals; treat exported spreadsheets as snapshots with an export timestamp, never as live data.
4. Use Moneycontrol only if a supported API/feed and reuse permission are provided. Do not scrape protected pages or reverse-engineer private endpoints.
5. Keep feed credentials server-side in GitHub Actions secrets / backend secret storage. Never embed them in APK assets or source.
6. Fail closed: if a provider is unavailable, show Unavailable, source, last verified timestamp, and retry status; never substitute another provider or relabel stale data as live.
7. Add contract tests for missing fields, numeric units, timestamps, stale responses, rate limits, and provider errors. Validate RSI, moving averages, and Nadaraya–Watson Envelope against a fixed known OHLCV dataset.

## Release gate
Do not label the build live-data verified until:
- the licensed provider is configured,
- quote/index timestamps are independently checked,
- chart candles match the licensed source,
- Screener fundamental values are reconciled against the displayed company page/export,
- tests and Android emulator smoke test pass on the exact release commit.