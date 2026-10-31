#!/usr/bin/env bash
set -euo pipefail
APK="app/build/outputs/apk/debug/app-debug.apk"
PACKAGE="com.prostock.intelligence"
ACTIVITY="com.prostock.intelligence/.MainActivity"
mkdir -p app/build/outputs

# Always preserve diagnostics, including when the renderer crashes or the DOM check fails.
capture_android_diagnostics() {
  adb logcat -d -t 12000 > app/build/outputs/psi-emulator-logcat.txt 2>&1 || true
  adb logcat -b crash -d > app/build/outputs/psi-emulator-crash-buffer.txt 2>&1 || true
  adb shell dumpsys meminfo "$PACKAGE" > app/build/outputs/psi-app-meminfo.txt 2>&1 || true
  adb shell dumpsys webviewupdate > app/build/outputs/psi-webview-provider.txt 2>&1 || true
  adb shell dumpsys activity activities > app/build/outputs/psi-activity-dump.txt 2>&1 || true
}
trap capture_android_diagnostics EXIT
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

# The emulator action can report "booted" before system_server has finished
# publishing package/activity services. Do not send key events or install while
# those services are absent: that caused Broken pipe / "Can't find service"
# failures before the app was ever launched.
adb wait-for-device
boot_ready=0
for attempt in $(seq 1 60); do
  boot_state="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  if [[ "$boot_state" == "1" ]] &&
     adb shell service check package 2>/dev/null | grep -qi "found" &&
     adb shell service check activity 2>/dev/null | grep -qi "found"; then
    boot_ready=1
    break
  fi
  sleep 3
done
if [[ "$boot_ready" -ne 1 ]]; then
  echo "Android system services did not become ready; refusing to attempt APK install"
  adb logcat -d -t 3000 || true
  exit 1
fi
service_check activity
service_check package
# Wake and dismiss the emulator lock screen before launching the dashboard.
# Some headless AVD snapshots report the Activity as resumed while the keyguard
# is still showing, which makes the DOM smoke test a false failure.
adb shell input keyevent KEYCODE_WAKEUP || true
adb shell wm dismiss-keyguard || true
adb shell input keyevent 82 || true
adb shell settings put system screen_off_timeout 600000 || true
sleep 2
adb shell settings put global window_animation_scale 0 || true
adb shell settings put global transition_animation_scale 0 || true
adb shell settings put global animator_duration_scale 0 || true

installed=0
for attempt in 1 2 3 4; do
  if adb install -r "$APK"; then installed=1; break; fi
  sleep 5
done
if [[ "$installed" -ne 1 ]]; then echo "APK installation failed after 4 attempts"; adb logcat -d -t 1200 || true; exit 1; fi

adb shell am force-stop "$PACKAGE" || true
adb logcat -c
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

# Foreground Activity is not enough: require the local dashboard DOM to finish loading.
# This catches splash-only launches and WebView/asset-loader failures that a valid PNG misses.
dashboard_ready=0
for attempt in $(seq 1 45); do
  if adb logcat -d -s PSI_STARTUP:E PSI_WEB:E AndroidRuntime:E | grep -Fq "PSI_DASHBOARD_DOM_READY"; then
    dashboard_ready=1
    break
  fi
  if ! adb shell pidof "$PACKAGE" >/dev/null 2>&1; then
    echo "Dashboard startup aborted: Android app process exited before DOM readiness (attempt $attempt)"
    break
  fi
  sleep 2
done
adb logcat -d -t 12000 > app/build/outputs/psi-emulator-logcat.txt || true
adb logcat -b crash -d > app/build/outputs/psi-emulator-crash-buffer.txt 2>&1 || true
if [[ "$dashboard_ready" -ne 1 ]]; then
  echo "Dashboard readiness failed: WebView did not confirm the app root DOM. Refusing to publish screenshot as a successful smoke test."
  echo "--- Relevant Android logcat ---"
  grep -E "PSI_STARTUP|PSI_WEB|FATAL EXCEPTION|AndroidRuntime|chromium|WebView|net::ERR" app/build/outputs/psi-emulator-logcat.txt | tail -n 250 || true
  echo "--- Last 250 logcat lines ---"
  tail -n 250 app/build/outputs/psi-emulator-logcat.txt || true
  exit 1
fi
adb exec-out screencap -p > app/build/outputs/psi-emulator.png
if ! xxd -p -l 8 app/build/outputs/psi-emulator.png | grep -qi "^89504e470d0a1a0a$"; then
  echo "Valid emulator screenshot check failed: invalid PNG"
  exit 1
fi
echo "Valid emulator screenshot: Activity foreground + dashboard DOM ready + PNG signature verified"
