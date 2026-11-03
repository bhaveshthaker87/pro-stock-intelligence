#!/usr/bin/env bash
set -euo pipefail

: "${ANDROID_HOME:?\$ANDROID_HOME must be set}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_HOME
SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
if [[ ! -x "$SDKMANAGER" ]]; then SDKMANAGER="$(command -v sdkmanager || true)"; fi
[[ -x "$SDKMANAGER" ]] || { echo "::error::sdkmanager executable not found"; exit 1; }
command -v emulator >/dev/null || { echo "::error::Android emulator executable missing"; exit 1; }
command -v avdmanager >/dev/null || { echo "::error::avdmanager executable missing"; exit 1; }

echo "Disk space before emulator SDK install:"
df -h "$ANDROID_HOME"
df -Pk "$ANDROID_HOME" | awk 'NR==2 { if ($4 < 6000000) { print "::error::Less than 6 GB free for emulator system image"; exit 1 } }'

IMAGE_ID="system-images;android-34;google_apis;x86_64"
IMAGE_DIR="$ANDROID_HOME/system-images/android-34/google_apis/x86_64"
valid_image() {
  [[ -s "$IMAGE_DIR/system.img" ]] &&
  [[ -s "$IMAGE_DIR/ramdisk.img" ]] &&
  [[ -s "$IMAGE_DIR/kernel-ranchu" || -s "$IMAGE_DIR/kernel-ranchu-64" ]] &&
  [[ -s "$IMAGE_DIR/source.properties" ]] &&
  grep -q 'Pkg.Revision' "$IMAGE_DIR/source.properties" &&
  [[ -s "$IMAGE_DIR/package.xml" ]]
}

if ! valid_image; then
  echo "System image missing or incomplete; removing only this package and SDK download cache."
  "$SDKMANAGER" --uninstall "$IMAGE_ID" >/dev/null 2>&1 || true
  rm -rf "$IMAGE_DIR"
  rm -rf "$HOME/.android/cache"
  mkdir -p "$HOME/.android/cache"
  installed=0
  for attempt in 1 2 3; do
    echo "Installing $IMAGE_ID (attempt $attempt/3)"
    if yes | "$SDKMANAGER" --install "$IMAGE_ID" --channel=0 --verbose; then
      if valid_image; then installed=1; break; fi
      echo "::warning::sdkmanager returned success but system-image integrity validation failed."
    else
      echo "::warning::sdkmanager system-image install failed on attempt $attempt."
    fi
    rm -rf "$IMAGE_DIR"
    if [[ "$attempt" -lt 3 ]]; then
      rm -rf "$HOME/.android/cache"
      mkdir -p "$HOME/.android/cache"
      sleep $((attempt * 20))
    fi
  done
  [[ "$installed" -eq 1 ]] || { echo "::error::Unable to install a valid Android 34 Google APIs x86_64 system image after 3 attempts."; exit 1; }
fi

sdkmanager --install 'emulator' 'platform-tools' 'platforms;android-34' --channel=0
valid_image || { echo "::error::Android system image failed final integrity validation"; exit 1; }
emulator -version
adb version
sdkmanager --list_installed | grep -F "$IMAGE_ID"
echo "Validated emulator, platform-tools and $IMAGE_ID"
