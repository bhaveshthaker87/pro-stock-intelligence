#!/usr/bin/env bash
set -euo pipefail
mkdir -p app/build/outputs
adb wait-for-device
boot_ready=0
for attempt in $(seq 1 180); do
  boot_state="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  if [[ "$boot_state" == "1" ]]; then boot_ready=1; break; fi
  sleep 3
done
if [[ "$boot_ready" != "1" ]]; then
  echo "Emulator boot timed out."
  adb devices -l || true
  adb logcat -d -t 500 || true
  exit 1
fi
services_ready=0
for attempt in $(seq 1 30); do
  package_ready="$(adb shell service check package 2>/dev/null || true)"
  activity_ready="$(adb shell service check activity 2>/dev/null || true)"
  if grep -q 'found' <<<"$package_ready" && grep -q 'found' <<<"$activity_ready"; then services_ready=1; break; fi
  sleep 2
done
if [[ "$services_ready" != "1" ]]; then
  echo "Android package/activity services did not become ready."
  adb shell service list || true
  adb logcat -d -t 800 || true
  exit 1
fi
installed=0
for attempt in 1 2 3 4; do
  if adb install -r app/build/outputs/apk/debug/app-debug.apk; then installed=1; break; fi
  echo "APK install attempt $attempt failed; retrying after emulator health check."
  adb wait-for-device || true
  sleep $((attempt * 3))
  boot_state="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  package_ready="$(adb shell service check package 2>/dev/null || true)"
  if [[ "$boot_state" != "1" ]] || ! grep -q 'found' <<<"$package_ready"; then
    adb devices -l || true
    adb logcat -d -t 1000 || true
  fi
done
if [[ "$installed" != "1" ]]; then
  echo "APK installation failed after 4 attempts."
  adb shell pm path com.prostock.intelligence || true
  adb shell service list || true
  adb logcat -d -t 1200 || true
  exit 1
fi
adb shell am force-stop com.prostock.intelligence
adb shell am start -W -n com.prostock.intelligence/.MainActivity
python3 -m pip install --quiet pillow numpy
dashboard_ready=0
for attempt in $(seq 1 30); do
  if adb shell dumpsys activity activities 2>/dev/null | grep -q 'com.prostock.intelligence/.MainActivity'; then
    adb exec-out screencap -p > app/build/outputs/psi-emulator.png
    if python3 -c 'from PIL import Image; import numpy as np; a=np.asarray(Image.open("app/build/outputs/psi-emulator.png").convert("RGB")); nonwhite=float((a < 245).any(axis=2).mean()); colors=int(np.unique(a.reshape(-1,3),axis=0).shape[0]); print("Visual readiness: nonwhite={:.3f}, colors={}".format(nonwhite,colors)); raise SystemExit(0 if nonwhite > 0.05 and colors > 2500 else 1)'; then dashboard_ready=1; break; fi
  fi
  sleep 2
done
if [[ "$dashboard_ready" != "1" ]]; then
  adb logcat -d -s PSI_WEB:E AndroidRuntime:E chromium:E || true
  echo "Dashboard did not render; screenshot remained blank or visually incomplete."
  exit 1
fi
test -s app/build/outputs/psi-emulator.png
python3 -c 'from pathlib import Path; p=Path("app/build/outputs/psi-emulator.png"); data=p.read_bytes(); assert data.startswith(bytes.fromhex("89504e470d0a1a0a")), "Emulator screenshot is not a valid PNG"; print("Valid emulator screenshot — rendered app: {} ({} bytes)".format(p, len(data)))'
