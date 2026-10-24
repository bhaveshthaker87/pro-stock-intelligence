#!/usr/bin/env bash
set -euo pipefail
APK="app/build/outputs/apk/debug/app-debug.apk"
PACKAGE="com.prostock.intelligence"
ACTIVITY="com.prostock.intelligence/.MainActivity"
mkdir -p app/build/outputs
if [[ ! -f "$APK" ]]; then echo "Debug APK missing: $APK"; exit 1; fi

service_check() {
  local kind="$1"
  local attempt
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if [[ "$kind" == "package" ]]; then
      # Check the Android package service and verify that the app is installed.
      adb shell service check package 2>/dev/null | grep -qi "found" &&
        adb shell cmd package list packages 2>/dev/null | grep -q "package:${PACKAGE}" && return 0
    else
      adb shell service check activity 2>/dev/null | grep -qi "found" && return 0
    fi
    sleep 3
  done
  echo "Android service check failed: $kind"
  adb logcat -d -t 1200 || true
  return 1
}

service_check activity
adb shell settings put global window_animation_scale 0 || true
adb shell settings put global transition_animation_scale 0 || true
adb shell settings put global animator_duration_scale 0 || true

installed=0
for attempt in 1 2 3 4; do
  if adb install -r "$APK"; then installed=1; break; fi
  sleep 5
done
if [[ "$installed" -ne 1 ]]; then echo "APK installation failed after 4 attempts"; adb logcat -d -t 1200 || true; exit 1; fi

service_check package
adb shell am force-stop "$PACKAGE" || true
adb shell am start -W -n "$ACTIVITY"

# Verify the requested Activity actually becomes foreground; a successful am start
# alone can still hide a crash, redirect, or immediate Activity finish.
foreground=0
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  adb shell dumpsys activity activities > app/build/outputs/psi-activity-dump.txt 2>&1 || true
  if grep -Eqi "mResumedActivity|topResumedActivity|Resumed:" app/build/outputs/psi-activity-dump.txt &&
     grep -Fq "com.prostock.intelligence" app/build/outputs/psi-activity-dump.txt; then
    foreground=1
    break
  fi
  sleep 2
done
if [[ "$foreground" -ne 1 ]]; then
  echo "Valid emulator screenshot blocked: app Activity did not become foreground"
  cat app/build/outputs/psi-activity-dump.txt || true
  adb logcat -d -t 1200 || true
  exit 1
fi

sleep 8
adb logcat -d -t 1200 > app/build/outputs/psi-emulator-logcat.txt || true
adb exec-out screencap -p > app/build/outputs/psi-emulator.png
if ! xxd -p -l 8 app/build/outputs/psi-emulator.png | grep -qi "^89504e470d0a1a0a$"; then
  echo "Valid emulator screenshot check failed: invalid PNG"
  exit 1
fi
echo "Valid emulator screenshot: app Activity reached foreground and PNG signature verified"
