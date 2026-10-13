# Pro Stock Intelligence V40.71 — Full-App Upgrade & Test Report

**Audit date:** 2026-10-11  
**Base:** Existing V40.70 source tree, audited before changes.  
**Artifact:** Source ZIP, not a signed APK.

## Executive result

V40.71 is a more testable source candidate. It adds a user-controlled CSV ingestion path, fixes a confirmed fiscal-column alignment risk, allows Android landscape orientation, and strengthens data provenance/failure labels. It does **not** establish 10/10 readiness: no live 30-stock data reconciliation, licensed Moneycontrol feed, Android Gradle build, lint run, or device/emulator run has been completed in this environment.

## Audit findings before editing

1. Screener fundamentals are parsed from authenticated website HTML; this is not a documented API, and broad all-stock accuracy was not independently proven.
2. No Moneycontrol adapter or authorized data feed was configured. The official [Moneycontrol Terms of Use](https://www.moneycontrol.com/cdata/termsofuse.php) restrict automated extraction and machine-readable database use without prior express written permission. Subscription access alone does not prove that permission.
3. The Android activity was locked to portrait even though the chart UI had responsive styles.
4. Annual table helpers skipped blank cells and could treat an older fiscal column as the newest value. This could contaminate net profit, operating profit, current ratio, and interest coverage.
5. Quote freshness logic could treat some future timestamps as recent.
6. Cache-clear endpoint reported success although no persistent provider cache was configured.

## Implemented in V40.71

- **CSV ingestion UI:** Added Data Sources / CSV modal with source selector for Screener CSV, Moneycontrol CSV (only if the user's product offers a permitted export), and other authorized CSV. Added local storage, remove-imported-data action, explicit source/freshness caveat, and links to official sites.
- **Shared CSV parser:** Added `app/src/main/assets/csv-import.js` with quoted comma/newline support, delimiter detection, strict numeric parsing, symbol mapping, unit-aware market-cap handling, duplicate-symbol rejection, and OHLCV import with date sorting and basic OHLC consistency checks.
- **Data merge rules:** Imported fundamentals fill missing values only when the user has the fallback checkbox enabled. Live values are never overwritten. Cross-source discrepancies are flagged; imported field provenance includes source/header/unit/period/import timestamp where available. Missing provider as-of dates are not invented.
- **Android file picker:** Added WebView `onShowFileChooser` handling for a user-selected CSV. Credentials are never requested or embedded.
- **Landscape:** Removed the portrait-only activity lock and improved narrow-screen placement of source controls.
- **Fiscal alignment:** Latest annual metric and derived-ratio calculations now use the newest fiscal cell only; a blank latest cell remains unavailable instead of silently shifting to an older period.
- **Timestamp quality:** Timestamps more than 60 seconds in the future are invalid; a small clock-skew case is not represented as verified real-time data.
- **Cache status:** The app no longer claims a provider cache was cleared when no persistent provider cache exists.
- **Release consistency:** UI/native engine/build version aligned to `40.71`; Android `versionCode` is `70`; CI artifact names aligned. CI syntax validation includes the new CSV parser.
- **Guides:** Added `SCREENER_MONEYCONTROL_CSV_IMPORT_GUIDE.md` and a blank `SCREENER_MONEYCONTROL_CSV_TEMPLATE.csv`.

## Actual local validation

- `python -m pytest -q tests`: **68 passed**.
- `python -m unittest discover -s tests -q`: **68 passed**.
- Browser smoke tests cover the CSV modal, file import/persistence, fundamental fallback, and user-imported OHLCV chart path with deterministic fixtures.
- `python -m py_compile tools/*.py tests/*.py`: **PASS**.
- `node --check` on both inline JavaScript blocks and `csv-import.js`: **PASS**.
- Android manifest XML parse: **PASS**.
- Version consistency and ZIP integrity: checked at packaging.

## Not verified / blocked

- **Moneycontrol automated integration:** Not implemented. The current official terms require written permission for automated extraction/database use. If your specific subscription offers a permitted CSV export, the app can import that file; otherwise an authorized feed/API or written permission is required.
- **Screener live session and all-stock accuracy:** Not tested with your authenticated account. Screener documents Premium CSV export and says it does not provide an API; HTML parsing can break if markup changes.
- **30-stock independent comparison:** Not run; no actual exports/session data were supplied to the build environment. Do not treat local mock tests as data accuracy evidence.
- **Gradle/Kotlin build, Android Lint, APK signing, emulator/device install, rotation test:** Not run because this environment has no `gradle`, `adb`, or `ANDROID_HOME` / Android SDK. No APK is claimed as built.
- **Technical indicator parity:** The chart UI is covered by existing smoke tests, but RSI/SMA/Nadaraya–Watson are not certified against a separately sourced golden OHLCV corpus in this release.

## Evidence-based rating at handoff

| Dimension | Rating | Reason |
|---|---:|---|
| Source architecture and regression safety | 7.5/10 | Strict failure behavior, field metadata, CSV tests, UI tests |
| CSV import/parser path | 7.5/10 | Local tests cover symbols, units, malformed values, duplicate rows, OHLCV and UI persistence; actual provider exports still need validation |
| Screener all-stock data accuracy | 4.5/10 | Live 30-stock reconciliation and authenticated markup fixtures are missing |
| Moneycontrol automated integration | 0/10 | No authorized feed/permission configured; manual permitted CSV import only |
| Chart/indicator verification | 6.0/10 | UI/interaction checks exist; golden-data parity not certified |
| Android release confidence | 3.5/10 | Manifest and JS checks pass, but Gradle/APK/device checks are blocked |
| **Overall release readiness** | **6.4/10** | Better source candidate; not a production-certified release |

## Release gates before claiming 10/10

- [ ] Obtain a documented, authorized Moneycontrol feed/API or written permission covering the intended extraction, storage, display, and redistribution. If only a permitted export is available, keep it as a user-imported source rather than claiming automated integration.
- [ ] Use real Screener and Moneycontrol samples/exports to validate header mappings, units, reporting periods and symbol identity.
- [ ] Reconcile at least 30 stocks at a common cutoff; report every field-level discrepancy with source, period, unit and as-of/fetch timestamp.
- [ ] Add real sanitized HTML/CSV fixtures for large/mid/small caps, banks, missing values, negative earnings and fiscal-period edge cases.
- [ ] Verify RSI(14), SMA50, SMA200 and Nadaraya–Watson against independent golden OHLCV datasets; confirm no look-ahead/repainting.
- [ ] Run clean Gradle build, Android Lint, dependency/security scan, APK install, portrait/landscape and offline/login-expiry tests in CI/device environment.
- [ ] Confirm every visible button/navigation path and release artifact checksum; document unresolved limitations and rollback steps.

**Bottom line:** V40.71 contains real source changes and 68 passing local tests, but it is not 10/10 yet. The biggest remaining blockers are authorized Moneycontrol data access, live stock-by-stock verification, and a real Android build/device run.
