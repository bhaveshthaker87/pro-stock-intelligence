#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
AVD_NAME="psi-ci"
IMAGE_ID="system-images;android-34;google_apis;x86_64"
OUT="app/build/outputs"
mkdir -p "$OUT"
EMULATOR_PID=""
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  echo "Emulator teardown (exit=$rc)"
  if [[ -n "$EMULATOR_PID" ]] && kill -0 "$EMULATOR_PID" 2>/dev/null; then
    adb -s emulator-5554 emu kill >/dev/null 2>&1 || true
    for _ in $(seq 1 15); do
      kill -0 "$EMULATOR_PID" 2>/dev/null || break
      sleep 1
    done
    kill "$EMULATOR_PID" 2>/dev/null || true
    wait "$EMULATOR_PID" 2>/dev/null || true
  fi
  adb logcat -d -t 12000 > "$OUT/psi-emulator-logcat.txt" 2>&1 || true
  adb logcat -b crash -d > "$OUT/psi-emulator-crash-buffer.txt" 2>&1 || true
  exit "$rc"
}
trap cleanup EXIT INT TERM

command -v emulator >/dev/null
command -v avdmanager >/dev/null
command -v adb >/dev/null
avdmanager create avd --force -n "$AVD_NAME" -k "$IMAGE_ID" -d pixel_2 <<< "no"
emulator -avd "$AVD_NAME" -port 5554 -no-window -no-audio -no-boot-anim -no-snapshot-load -no-snapshot-save -gpu swiftshader_indirect -memory 4096 -cores 4 -camera-back none -accel on > "$OUT/psi-emulator-startup.txt" 2>&1 &
EMULATOR_PID=$!
adb start-server
# Poll ADB and boot state in the bounded loop below; do not block forever in wait-for-device.
booted=0
for attempt in $(seq 1 120); do
  state="$(adb -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  status="$(adb devices | awk '$1=="emulator-5554" {print $2}')"
  if [[ "$state" == "1" && "$status" == "device" ]]; then booted=1; break; fi
  if ! kill -0 "$EMULATOR_PID" 2>/dev/null; then
    echo "::error::Emulator process exited before boot completed"
    cat "$OUT/psi-emulator-startup.txt" || true
    exit 1
  fi
  sleep 5
done
if [[ "$booted" -ne 1 ]]; then
  echo "::error::Emulator did not reach sys.boot_completed=1 with adb device online within 10 minutes"
  adb devices -l || true
  adb logcat -d -t 3000 > "$OUT/psi-emulator-boot-failure-logcat.txt" 2>&1 || true
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
