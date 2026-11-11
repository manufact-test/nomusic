#!/usr/bin/env bash
# Native ARMv7 own-source module witness on disposable ARM Android13 Redroid.
# No Yandex APK, account, song, HONOR phone or Play Protect changes.
set -euo pipefail
pkg="pro.celikom.armv7loaderhost.witness"
apk="$RUNNER_TEMP/celikom-armv7-witness-downloaded/CELIKOM-ARMv7-HOOK-WITNESS-Test.apk"
test "$GITHUB_ACTIONS" = true
test "$(uname -m)" = "aarch64"
test -f "$apk"
test "$(docker exec celikom-native-arm-android13 getprop sys.boot_completed 2>/dev/null)" = 1
test "$(docker exec celikom-native-arm-android13 getprop ro.build.version.sdk 2>/dev/null)" = 33

abi32="$(docker exec celikom-native-arm-android13 getprop ro.product.cpu.abilist32 2>/dev/null)"
if ! printf '%s' "$abi32" | grep -q 'armeabi-v7a'; then
  echo '{"result":"OWN_NATIVE_ARMV7_GUEST_ABI_MISSING","owner_phone_touched":false}'
  exit 2
fi
if docker exec celikom-native-arm-android13 pm path ru.yandex.music 2>/dev/null | grep -q 'package:'; then
  echo '{"result":"OWN_NATIVE_ARMV7_VENDOR_PACKAGE_PRESENT","owner_phone_touched":false}'
  exit 2
fi
docker cp "$apk" celikom-native-arm-android13:/data/local/tmp/own-armv7-witness.apk >/dev/null
install_result="$(docker exec celikom-native-arm-android13 pm install --user 0 /data/local/tmp/own-armv7-witness.apk 2>/dev/null || true)"
if ! printf '%s' "$install_result" | grep -q '^Success'; then
  echo '{"result":"OWN_NATIVE_ARMV7_APK_INSTALL_FAILED","owner_phone_touched":false}'
  exit 2
fi
installed="$(docker exec celikom-native-arm-android13 pm path "$pkg" 2>/dev/null || true)"
if [ "$(printf '%s\n' "$installed" | grep -c '^package:' || true)" != 1 ]; then
  echo '{"result":"OWN_NATIVE_ARMV7_INSTALL_IDENTITY_INVALID","owner_phone_touched":false}'
  exit 2
fi
docker exec celikom-native-arm-android13 logcat -c >/dev/null 2>&1
docker exec celikom-native-arm-android13 am start -W \
  -n "$pkg/pro.celikom.armv7loaderhost.MainActivity" >/dev/null 2>&1 || true
sleep 8
pid="$(docker exec celikom-native-arm-android13 pidof "$pkg" 2>/dev/null || true)"
alive=false
if [[ "$pid" =~ ^[0-9]+$ ]]; then alive=true; fi
activity="$(docker exec celikom-native-arm-android13 dumpsys activity activities 2>/dev/null || true)"
resumed=false
if printf '%s' "$activity" | grep -E 'mResumedActivity|topResumedActivity' | grep -q "$pkg/"; then
  resumed=true
fi
logs="$(docker exec celikom-native-arm-android13 logcat -d -s 'CelikomOwnHookWitness:I' '*:S' 2>/dev/null || true)"
hook=false
if printf '%s' "$logs" | grep -q 'RESULT=PASS CODE=OWN_MODULE_ACTIVITY_INTERCEPTED'; then hook=true; fi
# Strictly fixed verdicts. Never emit process IDs, raw logcat, keys or binary.
if [ "$alive" = true ] && [ "$hook" = true ]; then
  echo "{\"result\":\"OWN_NATIVE_ARMV7_LSPATCH_MODULE_ENTERED\",\"native_armv7_guest\":true,\"main_alive\":$alive,\"activity_resumed\":$resumed,\"oncreate_intercepted\":$hook,\"signature_bypass\":0,\"module_count\":1,\"vendor_apk_installed\":false,\"play_protect_tested\":false,\"audio_substitution_tested\":false,\"owner_phone_touched\":false}"
else
  echo "{\"result\":\"OWN_NATIVE_ARMV7_MODULE_GATE_FAILED\",\"native_armv7_guest\":true,\"main_alive\":$alive,\"activity_resumed\":$resumed,\"oncreate_intercepted\":$hook,\"vendor_apk_installed\":false,\"owner_phone_touched\":false}"
  exit 2
fi
