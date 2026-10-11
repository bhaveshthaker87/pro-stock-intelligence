# Pro Stock Intelligence — Production Release Evidence

**Evidence date:** 2026-10-11  
**Local candidate:** V40.63 (`versionName=40.63`, `versionCode=62`)  
**Current status:** hardened candidate; **not production-certified**

## Evidence verified in this session

### Local V40.63 source package

- `python -m pytest -q`: **36 passed**.
- `python -m unittest discover -s tests -q`: **36 passed**.
- Python source compilation (`python3 -m py_compile tools/*.py tests/*.py`): **PASS**.
- Inline JavaScript: 2 script blocks extracted and passed `node --check`.
- Android manifest XML parsing: **PASS**.
- ZIP integrity: **PASS**.
- ZIP SHA-256: `a1aa9382cbdd3841b42ab0d5642fad7ea25760ff9c86f3b2ef9578e427ec951d`.

These local tests validate code structure and deterministic fixtures; they do not validate vendor data accuracy, market-data licensing, profitable trading performance, or Android runtime behavior.

### GitHub repository and CI

Repository: https://github.com/bhaveshthaker87/pro-stock-intelligence  
Default branch: `main`  
Observed main commit: `67119e5ec75d1f7dd63d6c0bb29ec67255ba4129`

- GitHub Actions run #27 completed successfully: https://github.com/bhaveshthaker87/pro-stock-intelligence/actions/runs/38071896905
- Steps verified as successful: checkout, Java setup, Android SDK install/verification, Gradle setup, APK build, and artifact upload.
- Uploaded artifact: `PRO-STOCK-INTELLIGENCE-APK`, 1,334,768 bytes, SHA-256 digest reported by GitHub for the artifact ZIP: `5473b81d629e1f71d4a086961972f78c363fe73f5047f31233b67302ee80720a`.
- Artifact expiration shown by GitHub: 2026-10-17.
- Important scope limit: this workflow run **did not** execute browser tests, Android lint, emulator install/launch, screenshot checks, or live provider validation.
- The repository's current README reports V40.53 while `app/build.gradle` reports V40.52. The successful APK therefore is **not evidence for the local V40.63 candidate**.

## Release gate matrix

| Gate | Status | Evidence / blocker |
|---|---|---|
| Local automated tests | PASS | 36/36 pytest and unittest tests pass on local V40.63 source. |
| Static JavaScript/XML/package checks | PASS | Inline JS syntax, manifest parse, ZIP integrity pass. |
| Android Gradle build for V40.63 | NOT VERIFIED | Local environment lacks Gradle/Android SDK; remote successful build was for stale `main`, not V40.63. |
| Emulator install and launch for V40.63 | NOT VERIFIED | No successful emulator run evidence for V40.63. |
| Moneycontrol integration | BLOCKED | No Moneycontrol API documentation, endpoint contract, authentication scheme, or sanitized real response sample supplied to implement safely. No vendor secret is embedded in the APK. |
| Corporate event calendar | BLOCKED | No verified authorized feed configured for results, board meetings, dividends, splits, bonuses and rights issues. Empty data must not be interpreted as “no events”. |
| Strategy performance | BLOCKED | No point-in-time factor-score history, survivorship-aware universe including delisted securities, verified adjusted returns and realistic cost dataset provided. No profitability claim justified. |
| GitHub branch/PR write | BLOCKED | GitHub API branch creation returned HTTP 403 `Resource not accessible by integration`; no repository changes were pushed. Avoided direct commits to `main`. |
| Signed release / SBOM / independent review | NOT DONE | Release signing, dependency/SBOM audit and independent security review remain required. |

## Required next inputs

1. **Moneycontrol API integration:** provide the official/vendor API documentation or OpenAPI spec and a sanitized sample response (remove tokens, cookies, personal information and account identifiers). State which quote, history, corporate-action and results endpoints are included in the subscription. Never paste the API secret into chat or commit it to the repository.
2. **Server-side gateway:** provide the intended HTTPS backend hosting location (or approve a deployment target). Provider credentials must be stored as server-side environment secrets. The Android APK should call the gateway and contain no vendor API key.
3. **GitHub write permission:** enable repository write access for the connected GitHub integration, or create a branch and grant the integration permission to push. This is required to open a reviewable PR; no direct `main` commit was attempted.

## Release decision

The local V40.63 candidate is materially better hardened and has a passing 36-test local suite. The existing GitHub repository remains behind it, and its latest successful APK build is for the older main-branch source. A 10/10 or production-ready label is not supported until the source is synchronized, CI/emulator tests pass on that exact commit, and the authorized data feed, event calendar, and real historical backtest evidence are verified.
