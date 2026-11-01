$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Create a persistent Android upload key without installing Java on Windows.
# The JDK is downloaded as a temporary ZIP, used, and left uninstalled.
$work = Join-Path $env:TEMP "psi-portable-jdk17"
$zip = Join-Path $env:TEMP "psi-portable-jdk17.zip"
$keyFile = Join-Path (Get-Location) "psi-release.p12"

if (Test-Path $keyFile) {
    throw "Refusing to overwrite $keyFile. Move the existing key to a secure backup first."
}

Write-Host "Downloading a temporary Eclipse Temurin JDK 17 (no installation)..."
$url = "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse"
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory -Path $work | Out-Null
Expand-Archive -Path $zip -DestinationPath $work -Force
$keytool = Get-ChildItem -Path $work -Filter keytool.exe -Recurse | Select-Object -First 1 -ExpandProperty FullName
if (-not $keytool) { throw "keytool.exe was not found in the downloaded JDK." }

Write-Host ""
Write-Host "Create your own strong password when keytool prompts. Use at least 16 characters."
Write-Host "The key password will use the same password as the keystore password."
Write-Host "Do NOT share the password or keystore in chat."
& $keytool -genkeypair -v -keystore $keyFile -storetype PKCS12 -alias psi-release -keyalg RSA -keysize 3072 -validity 10000 -dname "CN=Pro Stock Intelligence, OU=Android, O=Pro Stock Intelligence, L=Ahmedabad, ST=Gujarat, C=IN"
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $keyFile)) {
    throw "Keystore generation failed. No key was created."
}

Write-Host "Verifying generated keystore..."
& $keytool -list -keystore $keyFile -alias psi-release
if ($LASTEXITCODE -ne 0) { throw "Keystore verification failed." }

[Convert]::ToBase64String([IO.File]::ReadAllBytes($keyFile)) | Set-Clipboard
Write-Host ""
Write-Host "SUCCESS: psi-release.p12 created and verified."
Write-Host "The Base64 keystore value is now in your clipboard."
Write-Host "Keep psi-release.p12 in a secure offline backup. Do not commit it to Git."
Write-Host "Next: add the four GitHub Actions secrets described in ANDROID_SIGNING_SETUP.md."
Remove-Item $zip -Force -ErrorAction SilentlyContinue
