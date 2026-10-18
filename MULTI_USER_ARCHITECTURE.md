# Multi-user production architecture (V40.80)

## Product requirement
PRO STOCK INTELLIGENCE is intended for multiple independent users, not only the developer's personal m.Stock account. Do not use one individual's broker API key, password, OTP, access token, or cookies as shared credentials for the whole user base.

## Two separate data-access models

### A. Shared market-data service (default for all app users)
- Obtain written authorization / suitable market-data rights for the intended multi-user display, redistribution, caching, history, and corporate-events use.
- Use a server-side provider gateway. The Android app calls only our HTTPS gateway; provider credentials remain in server-side secret storage.
- Authenticate app users, apply per-user rate limits and abuse protection, validate every response, and record source + as-of timestamp + real-time/delayed/EOD status.
- Do not ship provider secrets in the APK, JavaScript, Gradle properties, public repository, logs, or crash reports.
- Do not use public website scraping or a personal paid website login as an assumed API license.
- Until a shared feed is approved and configured, show a truthful unavailable state; never invent or mislabel prices/candles.

### B. Optional user-specific m.Stock account linking
- m.Stock's standard Trading API key/session is tied to an individual account and must not be shared among users.
- For a public third-party platform integration, contact m.Stock Partner Integration at tradingapi@mstock.com and request the official partner/platform onboarding flow, platform key, redirect URI registration, token handling requirements, and written permission for the planned use.
- Each end user must authenticate and consent through the provider-approved flow. Keep each user's tokens isolated, encrypted at rest, server-side only, and revocable; never ask users to paste credentials into our app/chat.
- Account linking is optional and separate from the shared market-data service. Do not require every app user to have an m.Stock account unless product policy and provider terms explicitly require it.
- Do not enable order placement in the initial release. Market-data access and trading permissions must be reviewed separately.

## Required multi-user security controls
- Server-side secret manager / environment secrets; HTTPS only.
- Per-user authentication and authorization; least-privilege scopes.
- Per-user rate limits, provider-wide rate limits, timeouts, bounded retries, and circuit breaker.
- Encrypt sensitive user-linked tokens at rest; never log passwords, OTPs, API keys, access tokens, refresh tokens, or full authorization headers.
- Token expiry, revocation, logout, and account unlinking flows.
- Privacy notice, data retention/deletion policy, terms of use, and incident response contact before public launch.
- Keep market data, user portfolio/account data, and app analytics logically separated.
- Do not expose one user's portfolio, holdings, account data, or provider tokens to another user.

## Release gates
1. Written provider authorization and documented permitted usage for a multi-user app.
2. Deployed HTTPS gateway with production authentication, secret storage, monitoring, and rate limits.
3. Sanitized real provider fixtures pass the quote/history/index/events validators.
4. Integration tests cover unauthenticated users, cross-user data isolation, token expiry/revocation, 403/429/5xx, timeouts, stale/future timestamps, malformed payloads, and provider outage.
5. Verify APK/source contains no provider secrets.
6. Emulator smoke test passes; live end-to-end test is marked skipped, not passed, when no authorized gateway is configured.
7. Release notes document the provider, timestamp semantics, delayed-data status, limitations, and privacy/data handling.

## Current status
This document is an architecture requirement, not evidence that a provider contract, partner platform key, backend, or live feed is already active. Production live data remains blocked until the applicable provider access and deployment gates pass.
