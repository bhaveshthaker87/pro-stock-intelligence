# V40.90 — Read-only Options Signals foundation

## Implemented in this candidate
- Adds an Options Signals workspace inside the Android dashboard.
- Lists m.Stock and Motilal Oswal as separate future market-data adapters.
- Displays the truthful state: API keys not generated; no authorized live feed; no signals.
- Adds a contract watchlist input area and signal/performance layout.
- Keeps order placement out of scope and disabled by design.
- Does not collect broker credentials or tokens in the Android APK.

## Not yet live
- Broker API keys are not generated.
- Market-data-only static-IP eligibility has not been confirmed by either broker.
- No broker authentication, WebSocket session, option-chain parser, or live option price is active.
- The UI must not display BUY CALL / BUY PUT until real broker data is authenticated, timestamp-checked, contract-matched and validated.

## Next integration gate
1. Obtain written confirmation from each broker that market-data-only WebSocket access is permitted without a static IP.
2. Generate API keys only in the broker portals.
3. Provision a trusted HTTPS backend/secret store; never embed API secrets in the APK or GitHub source.
4. Implement broker adapters and binary WebSocket packet parsing where applicable.
5. Validate option instrument master, expiry, strike, CE/PE, LTP, bid/ask, volume and OI.
6. Add stale-feed blocking and reconnect/token-refresh tests.
7. Paper-trade signals and publish timestamped performance before actionable signal display.

## Safety
This version is a UI foundation, not a live trading signal release. No order endpoint or automatic order placement is included.
