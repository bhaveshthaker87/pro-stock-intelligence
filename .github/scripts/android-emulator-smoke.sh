#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
AVD_NAME="psi-ci"
IMAGE_ID="system-images;android-34;google_apis;x86_64"
OUT="app/build/outputs"
mkdir -p "$OUT"

# avdmanager and emulator must resolve the AVD from the same explicit directory.
# Hosted runners can expose different Android user-home variables between tools;
# relying on their implicit defaults caused "Unknown AVD name [psi-ci]".
export ANDROID_AVD_HOME="${ANDROID_AVD_HOME:-$HOME/.android/avd}"
mkdir -p "$ANDROID_AVD_HOME"
echo "Using ANDROID_AVD_HOME=$ANDROID_AVD_HOME"

EMULATOR_PID=""
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  echo "Emulator teardown (exit=$rc)"
  if [[ -n "$EMULATOR_PID" ]] && kill -0 "$EMULATOR_PID" 2>/dev/null; then
    timeout 10s adb -s emulator-5554 emu kill >/dev/null 2>&1 || true
    for _ in $(seq 1 15); do
      kill -0 "$EMULATOR_PID" 2>/dev/null || break
      sleep 1
    done
    kill "$EMULATOR_PID" 2>/dev/null || true
    wait "$EMULATOR_PID" 2>/dev/null || true
  fi
  timeout 10s adb logcat -d -t 12000 > "$OUT/psi-emulator-logcat.txt" 2>&1 || true
  timeout 10s adb logcat -b crash -d > "$OUT/psi-emulator-crash-buffer.txt" 2>&1 || true
  exit "$rc"
}
trap cleanup EXIT INT TERM

command -v emulator >/dev/null
command -v avdmanager >/dev/null
command -v adb >/dev/null

avdmanager create avd --force -n "$AVD_NAME" -k "$IMAGE_ID" -d pixel_2 <<< "no"
AVD_CONFIG="$ANDROID_AVD_HOME/$AVD_NAME.ini"
if [[ ! -s "$AVD_CONFIG" ]]; then
  echo "::error::avdmanager did not create expected AVD config: $AVD_CONFIG"
  find "$HOME/.android" -maxdepth 4 -name "$AVD_NAME.ini" -o -name config.ini 2>/dev/null | head -50 || true
  avdmanager list avd || true
  exit 1
fi
if ! emulator -list-avds | grep -Fxq "$AVD_NAME"; then
  echo "::error::Emulator cannot discover AVD '$AVD_NAME' from ANDROID_AVD_HOME=$ANDROID_AVD_HOME"
  emulator -list-avds || true
  exit 1
fi
echo "AVD preflight passed: $AVD_CONFIG"

emulator -avd "$AVD_NAME" -port 5554 -no-window -no-audio -no-boot-anim -no-snapshot-load -no-snapshot-save -gpu swiftshader_indirect -memory 4096 -cores 4 -camera-back none -accel on > "$OUT/psi-emulator-startup.txt" 2>&1 &
EMULATOR_PID=$!
timeout 10s adb start-server

# Every ADB probe is time-bounded: a wedged ADB shell must not consume the
# entire Actions step timeout while hiding the original emulator startup error.
booted=0
for attempt in $(seq 1 120); do
  if ! kill -0 "$EMULATOR_PID" 2>/dev/null; then
    echo "::error::Emulator process exited before boot completed"
    cat "$OUT/psi-emulator-startup.txt" || true
    exit 1
  fi
  state="$(timeout 12s adb -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  status="$(timeout 8s adb devices 2>/dev/null | awk '$1=="emulator-5554" {print $2}' || true)"
  if [[ "$state" == "1" && "$status" == "device" ]]; then booted=1; break; fi
  sleep 5
done
if [[ "$booted" -ne 1 ]]; then
  echo "::error::Emulator did not reach sys.boot_completed=1 with ADB device online within 10 minutes"
  timeout 10s adb devices -l || true
  timeout 10s adb logcat -d -t 3000 > "$OUT/psi-emulator-boot-failure-logcat.txt" 2>&1 || true
  cat "$OUT/psi-emulator-startup.txt" || true
  exit 1
fi
echo "Android emulator boot verified; ADB reports emulator-5554 device."
BUILD_SIGNED_RELEASE="${BUILD_SIGNED_RELEASE:-false}"
if [[ "$BUILD_SIGNED_RELEASE" == "true" ]]; then
  PSI_SMOKE_APK="app/build/outputs/apk/release/app-release.apk" bash .github/scripts/android-smoke-test.sh
else
  bash .github/scripts/android-smoke-test.sh
fi
