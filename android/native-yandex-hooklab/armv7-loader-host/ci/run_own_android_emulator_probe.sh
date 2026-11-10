#!/usr/bin/env bash
# One shell scope is REQUIRED: reactivecircus executes each script line
# separately via /usr/bin/sh -c when passed a multiline script.
set -euo pipefail

APK="android/native-yandex-hooklab/armv7-loader-host/app/build/outputs/apk/debug/app-debug.apk"
PKG="pro.celikom.armv7loaderhost.audio"
test -f "$APK"
test "$(adb shell getprop ro.build.version.sdk | tr -d '\r')" = 33
adb install -r "$APK"
test "$(adb shell pm path "$PKG" | grep -c 'package:')" = 1
adb logcat -c
adb shell am start -W -n "$PKG"/pro.celikom.armv7loaderhost.MainActivity --ez celikom_own_probe true

RESULT=""
for tick in $(seq 1 65); do
    RESULT="$(adb logcat -d -s CelikomOwnMediaProbe:D '*:S' | grep -E 'RESULT=(PASS|FAIL)' | tail -1 || true)"
    if [ -n "$RESULT" ]; then
        break
    fi
    sleep 1
done
# Only fixed enum verdict; never dump audio, buffers, original APK, or URLs.
echo "$RESULT" | sed -E 's/.*(RESULT=(PASS|FAIL) CODE=[A-Z0-9_]+).*/\1/'
echo "$RESULT" | grep -q 'RESULT=PASS CODE=OWN_DECODER_LIFECYCLE'
echo 'PASS: real Android 13 OWN MediaPlayer prepare, seek, pause, paused/playing source reload, Next B'
