# V40.66 — Equity Search and Emulator Capture Fix

Date: 2026-10-11

## Changes
- Fixed GitHub Actions emulator screenshot capture: use `adb exec-out screencap -p` and validate PNG signature rather than writing to `/sdcard`, which failed with `Permission denied`.
- Added broader Yahoo Finance equity search suggestions alongside the built-in fallback list. Search results preserve `.NS` / `.BO` listing suffixes so the selected listing can be passed into quote resolution.
- Prevented a `.BO` selection from being silently represented by the NSE public quote endpoint; BSE-specific selection uses the `.BO` third-party lookup path and is explicitly labelled as non-exchange-certified.
- Synchronized UI/native engine version strings and incremented Android version to code 65 / name 40.66.
- Added regression tests for screenshot capture, broad search/disclaimer, and version consistency.

## Validation
- `python -m pytest -q`: 41 passed.
- Workflow YAML and inline JavaScript syntax are additionally checked by GitHub Actions.
- Android Gradle build and emulator smoke test were not run in this local environment; must be verified by the next GitHub Actions run.

## Important limitations
- Yahoo Finance search is best-effort discovery, not a complete official NSE/BSE security master. It may omit or return duplicate/incorrectly mapped securities. NSE publishes an official securities-available-for-trading list: https://www.nseindia.com/static/market-data/securities-available-for-trading.
- The current quote implementation uses an NSE public website endpoint with Yahoo Finance fallback. It is not a licensed guaranteed real-time feed. NSE's official real-time subscription and data usage policy describe the authorized data route: https://www.nseindia.com/static/market-data/real-time-data-subscription and https://www.nseindia.com/static/market-data/nse-data-policy.
- A 10/10 live-data guarantee requires a licensed provider for the intended app display rights, server-side credentials, source timestamps, delay status, market calendar handling, outage tests, and end-to-end validation. This patch does not claim those requirements are complete.
