# Authorized provider gateway contract (V40.62)

## Why this exists
The Android app must not contain a vendor API secret. The app currently uses best-effort public-web/third-party fallbacks and does **not** have a licensed vendor configured. This contract makes data integration testable once a provider and subscription are selected; it does not magically create provider access.

## Required deployment architecture
1. Obtain a provider agreement that permits the intended display, storage, history, and corporate-event use. NSE describes an authorized-vendor route for real-time data and separate corporate-data products: https://www.nseindia.com/static/market-data/real-time-data-subscription and https://www.nseindia.com/static/market-data/corporate-data-subscription.
2. Deploy a server-side gateway on HTTPS. Store credentials in server environment/secrets only, never in Android resources, Gradle constants, JavaScript, or APK. Enforce authentication, per-user rate limits, symbol allowlists, response-size limits, request timeouts, and audit logs.
3. Adapt the vendor's documented schema to the normalized payloads below. Do not scrape protected pages or invent undocumented API endpoints.
4. Run `python tools/validate_provider_payloads.py quote quote.json`, `history history.json`, and `events events.json` on sanitized samples from the actual provider. The validator checks shape/freshness/consistency, not legal licensing or factual accuracy.
5. Keep the UI explicit about source, status, as-of timestamp, and delayed/EOD mode. If timestamp or status is absent, reject the quote as unverified rather than infer freshness from receipt time. Empty events means “no events returned”, not “no events exist”.

## Normalized JSON schemas

Quote: `{ "symbol":"INFY", "source":"Vendor Name", "asOf":"2026-10-11T09:15:00+05:30", "price":1500.25, "currency":"INR", "marketDataStatus":"REALTIME" }`. `marketDataStatus` must be `REALTIME`, `DELAYED`, or `EOD`. `DELAYED` requires integer `delayMinutes > 0`. Validator freshness limits are 5 minutes for real-time, 24 hours for delayed, and 72 hours for EOD; adjust only with a documented market calendar and product SLA.

History: same `symbol/source/asOf` metadata plus `interval` in `1m, 5m, 15m, 1d, 1wk, 1mo` and chronological `rows`, each with timezone-aware `time`, positive `open/high/low/close`, and nonnegative `volume`.

Events: same metadata plus `rows`; each row includes `symbol`, `eventType` (`RESULTS`, `DIVIDEND`, `SPLIT`, `BONUS`, `RIGHTS`, `BOARD_MEETING`, `OTHER`), `title`, timezone-aware `announcedAt`, and `eventDate` beginning with `YYYY-MM-DD`. Empty rows are allowed but never treated as proof of no events.

## Release gates
- Vendor contract/license reviewed and source identified in UI.
- Real sanitized fixtures from the provider pass validation.
- Provider outage, throttling, malformed JSON, stale timestamp, future timestamp, wrong symbol, and missing field tests pass.
- End-to-end live smoke test records source + timestamp without exposing credentials.
- No provider API key is present in source or built APK.


## Moneycontrol and Screener source limitation (V40.64)

The app must not treat a paid website login as permission to extract or redistribute structured data. Moneycontrol's published Terms of Use restrict automated extraction and machine-readable reuse without prior express written permission; Screener's published terms describe personal, non-commercial viewing and restrict copying/mirroring. This project therefore does not scrape Moneycontrol, invent undocumented endpoints, or label Yahoo/NSE fallback data as Moneycontrol data. The chart toolbar links directly to the relevant company/source search pages.

Before enabling structured Moneycontrol or Screener data in the gateway, provide the vendor's written authorization/API documentation, response schema, allowed use (personal display, storage, historical data and corporate events), and authentication requirements. Configure the vendor secret only in server-side environment secrets. The current APK intentionally contains no vendor credentials.
