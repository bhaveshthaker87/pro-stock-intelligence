# Pro Stock Intelligence V40.67 — Data Quality / Release Hardening Candidate

Date: 2026-10-11

## Changes implemented in this candidate
- Bumped Android version to versionCode 66 / versionName 40.67 and synchronized UI/native engine version markers.
- Added quote-quality metadata for the combined analysis and quote endpoints. The app distinguishes a missing provider quote timestamp from a recent timestamp and an older/future timestamp; it does not use response-received time as quote time.
- Added explicit quote age, timestamp source, and price-value validity diagnostics to returned quote payloads.
- Changed listing chips so the UI no longer unconditionally claims that every selected symbol is listed on both NSE and BSE. It displays the exchange inferred from the selected `.NS` / `.BO` symbol when present and otherwise states that BSE availability varies.
- Retained the V40.66 workflow fix that captures emulator screenshots with `adb exec-out screencap -p`, avoiding the `/sdcard` permission failure.
- Updated regression tests and artifact names for V40.67.

## Local validation performed
- `python -m pytest -q`: 43 passed.
- AndroidManifest XML parsed successfully.
- Extracted inline JavaScript blocks from dashboard HTML for syntax validation (see workflow for Node `--check`).
- ZIP integrity checked after packaging.

## Not verified in this environment
- Android Gradle build / Android lint / emulator run: Android SDK and Gradle are not installed in this environment. GitHub Actions must verify the actual APK.
- Live data correctness against a licensed exchange/vendor feed: not verified.
- Complete official NSE/BSE security master: not included. Existing suggestions combine a local tracked-symbol fallback with Yahoo Finance search, which is not an exhaustive or authoritative exchange list.
- Real-time data entitlement: not configured. NSE public website responses and Yahoo Finance can be delayed, blocked, incomplete, or schema-changed. Timestamp quality labels are diagnostics, not a real-time guarantee.
- Moneycontrol API: no documented, authorized provider endpoint or credentials were supplied/configured; do not represent Moneycontrol as integrated.
- Corporate events: third-party/history-derived events are not a complete official corporate-event calendar.
- Production security audit, signed release APK, point-in-time/survivorship-aware backtest, and real-device QA remain release gates.

## Release decision
This is a hardened release candidate, not a proven 10/10 or production-certified release. A complete 10/10 live-data claim requires a chosen licensed provider with display/storage rights, a deployed server-side gateway with credentials stored as secrets, official current NSE/BSE security master ingestion, real provider fixtures, end-to-end CI success, and user-device verification.
