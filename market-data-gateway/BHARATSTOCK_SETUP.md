# BharatStock EOD provider setup

The gateway supports BharatStock as an optional server-side EOD provider. It does not provide tick-by-tick or streaming prices.

## Configure the API key

1. Create a free key at https://bharatstockapi.com/.
2. In the repository's GitHub settings, open **Secrets and variables → Actions → New repository secret**.
3. Add the secret name `BHARATSTOCK_API_KEY` and paste the key into GitHub's secret-value field. Never commit the key or put it in Android/WebView code.
4. Configure the deployed HTTPS gateway environment with `BHARATSTOCK_API_KEY`. The Android app must call the gateway; the key must remain server-side.
5. Deploy/restart the gateway, then verify `/health` reports `bharatstock_configured: true`.
6. Test `/v1/quote?symbol=RELIANCE` and `/v1/history?symbol=RELIANCE&range=1y`. Confirm the source label says BharatStock EOD API and the timestamp is from provider data.

## Free-tier constraints

The documented free quota is 60 API requests per UTC day and historical time-series is limited to roughly one year. The quote adapter uses one ratios request per symbol. Do not poll every symbol repeatedly; use daily EOD refresh plus a server-side cache and refresh only on an appropriate cadence. Batch endpoints can be used for watchlists where supported.

## Honest data status

- Quotes and candles from this provider are EOD/daily, not tick-by-tick and not guaranteed real-time.
- A missing API key must never trigger fabricated values.
- A 401 indicates an invalid/missing key; a 429 means quota exhausted.
- Provider unit tests use mocked payloads. They prove mapping behavior only; they do not prove a real API key works or that all NSE/BSE listings are populated.
- The gateway's existing NSE public-web fallback remains unofficial and can be blocked. A green unit test is not live-provider verification.
