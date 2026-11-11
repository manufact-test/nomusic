#!/usr/bin/env bash
# Real ARM64 Linux -> containerized Android 13. NO user APK, Yandex or accounts.
# Only disposable GitHub Actions ARM VM; no phone/cloud account connection.
set -euo pipefail

if [ "${GITHUB_ACTIONS:-}" != "true" ] || [ "$(uname -m)" != "aarch64" ]; then
  echo '{"result":"NOT_DISPOSABLE_ARM64_CI","android_started":false}'
  exit 2
fi
if [ "$(getconf PAGESIZE)" != "4096" ]; then
  echo '{"result":"UNSUPPORTED_HOST_PAGE_SIZE","android_started":false}'
  exit 2
fi
sudo modprobe binder_linux devices=binder,hwbinder,vndbinder >/dev/null 2>&1
sudo mkdir -p /dev/binderfs
sudo mount -t binder binder /dev/binderfs
test -e /dev/binderfs/binder-control
docker info >/dev/null
echo '{"result":"NATIVE_ARM64_BINDERFS_READY","page_size":4096,"vendor_apk_downloaded":false}'

# Source: redroid 13 multi-arch official Docker manifest. Pinned by digest.
image="redroid/redroid@sha256:41e5f0c1ff27a4a474c474e5595168cedf6c40fc5dd102c5617f48c80f511e9e"
docker pull --platform linux/arm64 "$image" >/dev/null
arch="$(docker image inspect "$image" --format '{{.Architecture}}')"
if [ "$arch" != "arm64" ]; then
  echo '{"result":"CONTAINER_IMAGE_ARCH_NOT_ARM64","android_started":false}'
  exit 2
fi
mkdir -p "$RUNNER_TEMP/celikom-redroid-data"
if ! docker run -d --rm --privileged \
    --name celikom-native-arm-android13 \
    --network bridge \
    -p 127.0.0.1:5555:5555 \
    --mount type=bind,source=/dev/binderfs,target=/dev/binderfs \
    --mount type=bind,source="$RUNNER_TEMP/celikom-redroid-data",target=/data \
    "$image" androidboot.use_memfd=1 >/dev/null 2>&1; then
  echo '{"result":"CONTAINER_ANDROID_START_REJECTED","android_started":false}'
  exit 2
fi
boot=false
for attempt in $(seq 1 90); do
  if ! docker inspect celikom-native-arm-android13 --format '{{.State.Running}}' 2>/dev/null | grep -q '^true$'; then
    break
  fi
  state="$(docker exec celikom-native-arm-android13 getprop sys.boot_completed 2>/dev/null || true)"
  if [ "$state" = "1" ]; then boot=true; break; fi
  sleep 3
done
if [ "$boot" != "true" ]; then
  logs="$(docker logs --tail 200 celikom-native-arm-android13 2>&1 || true)"
  binder_problem=false
  if printf '%s' "$logs" | grep -iq 'binder.*\(failed\|not found\|could not\|permission denied\)'; then
    binder_problem=true
  fi
  echo "{\"result\":\"CONTAINER_ARM_ANDROID_NOT_BOOTED\",\"binder_error_marker\":$binder_problem,\"owner_phone_touched\":false,\"vendor_apk_installed\":false}"
  exit 2
fi
sdk="$(docker exec celikom-native-arm-android13 getprop ro.build.version.sdk 2>/dev/null || true)"
abi="$(docker exec celikom-native-arm-android13 getprop ro.product.cpu.abilist 2>/dev/null || true)"
abi32="$(docker exec celikom-native-arm-android13 getprop ro.product.cpu.abilist32 2>/dev/null || true)"
guest_kernel="$(docker exec celikom-native-arm-android13 uname -m 2>/dev/null || true)"
native64=false
native32=false
if [ "$guest_kernel" = "aarch64" ] && printf '%s' "$abi" | grep -q 'arm64-v8a'; then native64=true; fi
if printf '%s' "$abi32" | grep -q 'armeabi-v7a'; then native32=true; fi
if [ "$sdk" != "33" ] || [ "$native64" != "true" ]; then
  echo "{\"result\":\"CONTAINER_NATIVE_ANDROID_ABI_OR_VERSION_INVALID\",\"api33\":false,\"native64\":$native64,\"native32\":$native32,\"vendor_apk_installed\":false}"
  exit 2
fi
echo "{\"result\":\"NATIVE_ARM_ANDROID_13_CONTAINER_BOOTED\",\"sdk33\":true,\"native64\":$native64,\"native32\":$native32,\"ready_for_armv7_lspatch\":$native32,\"owner_phone_touched\":false,\"vendor_apk_installed\":false,\"account_tested\":false,\"audio_tested\":false,\"play_protect_tested\":false}"
