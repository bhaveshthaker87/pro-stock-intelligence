# Pro Stock Intelligence — experimental NSE gateway

Server-side adapter for public NSE website endpoints. Provides quote, daily history, corporate actions, announcements, board meetings and financial-result filing metadata.

## Important limits
- This is **not an official NSE API** and data is not guaranteed real-time, exchange-authorized, or verified. NSE may block/rate-limit/change endpoints; errors are returned instead of fabricated prices.
- `live_data_verified` intentionally remains `false` until production data is independently verified.
- Do not expose publicly without HTTPS, access controls, rate limiting and monitoring. Never place credentials in the Android APK.
- Screener authentication is separate and is not solved by this gateway.
- Review NSE terms and relevant licensing/usage requirements before production deployment.

## Run
```sh
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080
```

## Endpoints
- `GET /health`
- `GET /v1/quote/RELIANCE`
- `GET /v1/history/RELIANCE?from=01-10-2026&to=25-10-2026`
- `GET /v1/actions/RELIANCE?start=01-01-2026&end=25-10-2026`
- `GET /v1/announcements/RELIANCE?start=01-01-2026&end=25-10-2026`
- `GET /v1/board-meetings/RELIANCE?start=01-01-2026&end=25-10-2026`
- `GET /v1/results/RELIANCE?start=01-01-2026&end=25-10-2026`

Date format: DD-MM-YYYY. A successful HTTP response is not proof of data accuracy. Before the Android app consumes this service, deploy at an HTTPS URL, configure `PROVIDER_GATEWAY_BASE_URL`, and run real-provider contract verification.
