# Android signing setup (Windows, no Java installation)

The app's signed-release workflow uses a persistent upload key. This one-time setup downloads a temporary JDK 17 ZIP from Eclipse Adoptium, runs `keytool`, and does not install Java or modify PATH.

## 1. Generate your key

1. Open the repository's **Code** page and download this script: `tools/create-android-signing-key.ps1`.
2. Open PowerShell in a private folder where you want to keep the signing key.
3. Run:

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\create-android-signing-key.ps1
   ```

4. When prompted by keytool, create a strong password (at least 16 characters). Use the same password for the keystore and key.
5. The script creates `psi-release.p12`, verifies it, and copies its Base64 representation to the clipboard.

**Keep `psi-release.p12` and its password in a secure offline backup. Never commit the file or send it in chat.** If this key is lost, future updates signed with a different key may not install over the existing app.

## 2. Add GitHub Actions secrets

Open **Settings → Secrets and variables → Actions → New repository secret** in this repository. Add:

| Secret name | Value |
|---|---|
| `PSI_KEYSTORE_BASE64` | Paste the Base64 value already copied to your clipboard |
| `PSI_KEYSTORE_PASSWORD` | The password you entered in keytool |
| `PSI_KEY_ALIAS` | `psi-release` |
| `PSI_KEY_PASSWORD` | Same password as the keystore |

Do not put passwords in repository Variables, source files, workflow inputs, artifacts, or chat.

## 3. Signed release requirements

A signed production build also requires the repository variable `PROVIDER_GATEWAY_BASE_URL` to point to an authorized HTTPS data gateway whose quote, history, events, dividends and index payloads pass the repository validators. A signing key alone does not create or authorize market data.

After the four secrets and gateway variable are configured, open **Actions → Build PRO STOCK INTELLIGENCE APK → Run workflow**, select `build_signed_release`, and start the run. Download the signed APK and its SHA-256 checksum only after the workflow reports success and signature verification passes.

## 4. Data limitations

- NSE public historical files are EOD data, not an authorized real-time quote feed.
- The app must show unavailable/reference/EOD states honestly when a provider is not configured.
- Screener 403 responses must not be bypassed. Use the official site, permitted exports, or an authorized integration.
- A green Android build does not prove live market-data correctness or production readiness.
