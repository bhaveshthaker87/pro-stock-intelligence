# V40.78 — NSE/Screener-only provider policy and release status

## Changes in this candidate
- Bumped Android app version to 40.78 (versionCode 77).
- Aligned dashboard engine labels and GitHub Actions artifact names to V40.78.
- Disabled Yahoo Finance quote/history, news, and equity-search network adapters.
- Disabled automated requests to undocumented NSE public website API endpoints.
- Kept Screener.in fundamentals/session workflow as the only intended fundamentals source.
- Added regression assertions that Yahoo endpoints and the NSE quote endpoint are absent from the native provider source.

## Critical release blocker — no live market feed
The user has access to the public NSE website but has not configured an authorized NSE real-time or historical-data API/feed. Public website access is not proof of API authorization and does not provide a stable feed contract. Accordingly, V40.78 deliberately fails closed for NSE quotes, index snapshots, and historical candles rather than scraping the website, using Yahoo/Moneycontrol, or inventing data.

This means **V40.78 does not yet satisfy the requirement that live prices and chart parameters populate immediately**. A successful build cannot remove this blocker. An authorized NSE feed/vendor contract and integration credentials/configuration are required. Credentials must not be committed to the repository.

## Screener status
The existing in-app Screener login/session and HTML fundamentals parser remain. They must be validated with the user's actual signed-in session. A mocked CI test cannot prove the private Screener session works or that every requested fundamental is available.

## Verification status
- Source and version changes committed to the candidate branch.
- CI build, unit/UI tests, lint, and emulator smoke test: pending GitHub Actions.
- Real NSE live quote latency and complete parameter coverage: not verified; currently blocked by missing authorized feed.
- Screener authenticated end-to-end validation: not verified in CI.
- Do not publish this candidate as a live-data release until the blockers above are resolved.
