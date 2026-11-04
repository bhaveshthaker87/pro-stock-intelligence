#!/usr/bin/env bash
set -euo pipefail

: "${ANDROID_HOME:?\$ANDROID_HOME must be set}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_HOME
# sdkmanager does not update PATH after installing optional SDK packages.
SDK_PATHS=("$ANDROID_HOME/emulator" "$ANDROID_HOME/platform-tools" "$ANDROID_HOME/cmdline-tools/latest/bin")
for sdk_path in "${SDK_PATHS[@]}"; do
  if [[ -d "$sdk_path" ]]; then
    case ":$PATH:" in *":$sdk_path:"*) ;; *) export PATH="$sdk_path:$PATH" ;; esac
    if [[ -n "${GITHUB_PATH:-}" ]]; then printf '%s\n' "$sdk_path" >> "$GITHUB_PATH"; fi
  fi
done
SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
if [[ ! -x "$SDKMANAGER" ]]; then SDKMANAGER="$(command -v sdkmanager || true)"; fi
[[ -x "$SDKMANAGER" ]] || { echo "::error::sdkmanager executable not found"; exit 1; }
echo "Disk space before emulator system-image install:"
df -h "$ANDROID_HOME"
df -Pk "$ANDROID_HOME" | awk 'NR==2 { if ($4 < 6000000) { print "::error::Less than 6 GB free for emulator system image"; exit 1 } }'

# Install the emulator package before checking its executable. The base
# android-actions/setup-android step intentionally installs no optional packages.
"$SDKMANAGER" --install 'emulator' 'platform-tools' 'platforms;android-34' --channel=0

EMULATOR_BIN="$ANDROID_HOME/emulator/emulator"
AVDMANAGER_BIN="$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager"
[[ -x "$EMULATOR_BIN" ]] || { echo "::error::Android emulator package installed but $EMULATOR_BIN is missing or not executable"; find "$ANDROID_HOME/emulator" -maxdepth 2 -type f -name emulator -ls 2>/dev/null || true; exit 1; }
[[ -x "$AVDMANAGER_BIN" ]] || { echo "::error::avdmanager executable missing at $AVDMANAGER_BIN"; exit 1; }
[[ -x "$ANDROID_HOME/platform-tools/adb" ]] || { echo "::error::adb executable missing after platform-tools installation"; exit 1; }

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
    if "$SDKMANAGER" --install "$IMAGE_ID" --channel=0 --verbose; then
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

"$SDKMANAGER" --install 'platform-tools' 'platforms;android-34' --channel=0
valid_image || { echo "::error::Android system image failed final integrity validation"; exit 1; }
"$EMULATOR_BIN" -version
"$ANDROID_HOME/platform-tools/adb" version
"$SDKMANAGER" --list_installed | grep -F "$IMAGE_ID"
echo "Validated emulator, platform-tools and $IMAGE_ID"
