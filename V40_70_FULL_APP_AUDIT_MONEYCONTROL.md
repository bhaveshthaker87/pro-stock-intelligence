# Pro Stock Intelligence V40.70 — Full App Audit & Moneycontrol Integration Assessment

Audit date: 2026-10-11  
Audited artifact: source tree `V40_70/src` (not a signed APK)  
Audit approach: static source review + local automated checks. No live provider session, external credentials, Android SDK, Gradle installation, or device/emulator was available.

## Executive verdict

**Overall app rating: 6.1/10 (source-candidate quality; not production certification).**  
**Moneycontrol integration: 0/10 currently implemented.** The app itself explicitly reports `NOT INTEGRATED — NO VERIFIED ACCESS/FEED CONFIGURED`; this was confirmed in `MainActivity.kt`. Do not interpret Moneycontrol as a current source for any displayed metric.

The app has a broad, ambitious dashboard and some good fail-closed/data-provenance work. However, data-provider coverage, source entitlement, end-to-end accuracy evidence, release build verification, and real-device QA are not strong enough to call it 10/10.

## Category ratings

| Area | Rating | Evidence-based assessment |
|---|---:|---|
| UI / feature breadth | 7.5/10 | Broad dashboard, research cockpit, chart, financials, ownership, peers, news/events and scan screens exist in the HTML asset. Functional breadth is not proof every control works end-to-end. |
| Fundamental parsing safety | 7.0/10 | Screener HTML parsing checks company heading and expected ratios area; ambiguous values fail closed; CAGR period alignment was fixed. Real-world markup coverage is not proven. |
| Fundamental accuracy across stocks | 4.5/10 | No completed independent 30-stock, field-by-field source/period/unit reconciliation; current integration relies on unversioned page markup. |
| Quote / price provenance | 5.5/10 | App labels public NSE endpoint and Yahoo fallbacks, and marks uncertain timestamps; it does not use a verified licensed market-data feed. |
| Moneycontrol | 0/10 | Not integrated. No verified feed/API/license is configured. Moneycontrol must not be claimed as a source until an authorized integration is built and tested. |
| Chart / indicators | 6.0/10 | Chart workspace and indicators exist, but no supplied golden OHLCV parity report proving RSI/SMA/Nadaraya–Watson results against independently computed expected values. |
| Provider resilience | 6.0/10 | Errors and unavailable states exist, but live throttling, expiry, outage, cache/retry, wrong-symbol and provider-markup scenarios are not comprehensively validated end-to-end. |
| Automated regression tests | 8.0/10 | 55 local Python tests pass. These are largely source/regression tests and do not prove live source accuracy or APK behavior. |
| Security / secret handling | 7.0/10 | Existing docs require server-side secrets for a licensed gateway; app currently makes direct provider requests and has no configured licensed gateway. APK secret scan/build scan not performed. |
| Android build / install / device QA | 3.0/10 | No Gradle build, Android Lint, APK signing, emulator or real-device run was completed. |
| Release evidence / reproducibility | 4.0/10 | Local checks are repeatable; production build provenance and device evidence are missing. |

## Moneycontrol: what can and cannot be done now

Moneycontrol's official Terms of Use prohibit automated extraction/scraping and machine-readable database use without prior express written permission, and say other use may require prior written consent/fees. See:
- https://www.moneycontrol.com/cdata/termsofuse.php
- https://www.moneycontrol.com/cdata/disclaim.php?classic=true

Therefore, this audit does **not** add an undocumented Moneycontrol scraper or guess at private endpoints. That would be brittle and may violate the provider's terms. A compliant path is:

1. Obtain written permission and a documented feed/API/data licence that covers the intended fields, frequency, storage, display, and redistribution—or use a user-provided export only where the export terms permit it.
2. Build a Moneycontrol adapter against the authorized documented schema, not guessed page endpoints.
3. Normalize every metric with canonical symbol, exchange, source URL/provider ID, reported period (TTM/FY/quarter), unit/currency, as-of/fetched timestamp, and adjustment basis.
4. Add deterministic precedence rules. Example: show source-specific values side-by-side; never silently overwrite Screener values with Moneycontrol values when periods/units differ.
5. Add fixtures for 30+ stocks across sectors and missing/negative values, bank metrics, alternate labels, corporate actions, and different fiscal periods; compare field-by-field against the provider's original display/export.
6. Run live smoke tests, timeout/429/403/login-expiry tests, and verify stale data is labelled instead of presented as current.

Moneycontrol provides a public stock comparison page with metrics, but that is not itself an authorized API contract: https://www.moneycontrol.com/markets/compare/ind-cap-stocks-ICC05/

## Checks run for this audit

- `python -m pytest -q tests`: **55 passed**.
- Python syntax compilation for `tools/*.py` and `tests/*.py`: recorded in the run results below.
- Android manifest XML parse: recorded in the run results below.
- Inline JavaScript syntax check: recorded in the run results below.
- ZIP CRC/integrity: recorded in the run results below.
- Not run / not verified: Gradle/Kotlin build, Android Lint, APK generation/signing, emulator/device tests, live Screener session, Moneycontrol feed, live 30-stock comparison, chart indicator parity against golden OHLCV data.

## Release gates before claiming 10/10

- [ ] Authorized Moneycontrol data access/feed or written scraping permission verified.
- [ ] Screener access path and intended use validated against its current terms and user entitlement.
- [ ] 30+ stock source comparison report completed at a shared cutoff, including units and fiscal periods.
- [ ] Provider adapters reject wrong-symbol, stale, future-dated, malformed and mismatched-period data.
- [ ] Quote, fundamentals, financials, shareholding and corporate events show source + period + timestamp separately.
- [ ] Golden dataset tests verify RSI(14), SMA50, SMA200, and Nadaraya–Watson envelope calculations.
- [ ] Full Gradle build, lint, dependency/security checks, signed APK and checksum recorded.
- [ ] Android portrait/landscape, screen resize, offline, session expiry and accessibility smoke tests pass.
- [ ] All visible buttons/navigation tested end-to-end; no fake success states.
- [ ] Reproducible release report published with known limitations and rollback instructions.

## Final recommendation

Keep V40.70 as a **candidate for further testing**, not a production-grade 10/10 release. The best next step is not to scrape Moneycontrol blindly; it is to obtain an authorized data route and implement a source-aware dual-provider reconciliation layer. Until then, the app should clearly show Moneycontrol as “not integrated,” not as a live source.
