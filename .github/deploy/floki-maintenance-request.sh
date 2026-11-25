#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
base=/srv/celikom-releases/private/android-v95
[[ -d "$base" && ! -L "$base" && "$(stat -c '%u:%a' "$base")" == '0:700' ]]
printf '%s  %s\n' \
 d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469 "$base/CELIKOM-Android-0.3.94-SIGNED.apk" \
 8e5205b64ea65b8a9879b7034a3e5c141a8e96b79a0e1a07c1d849def358478e "$base/stable-floki-candidate.json" \
 011386d2bb9c1fdb504f2b802c590b2076f07a1132c79082282f4b8846fc005f "$base/stable-hostinger-bridge-candidate.json" | sha256sum -c --status
test "$(stat -c '%u:%a:%s' "$base/CELIKOM-Android-0.3.94-SIGNED.apk")" == 0:600:8845385
test "$(stat -c '%u:%a:%s' "$base/stable-floki-candidate.json")" == 0:600:520
test "$(stat -c '%u:%a:%s' "$base/stable-hostinger-bridge-candidate.json")" == 0:600:554
for path in /root/celikom-android-v95-intake/expires /usr/local/sbin/celikom-android-v95-receive /etc/sudoers.d/celikom-android-v95-receive; do
 [[ ! -e "$path" ]]
done
! grep -qF 'receive-android-v95-' /usr/local/sbin/celikom-deploy-gateway
echo ANDROID_V95_PRIVATE_STAGE_AND_TEMP_ADMIN_RECEIVER_CLOSED
echo ANDROID_PREPARED_NGINX_VERSION93_REFERENCE
sed -n '1,120p' /root/celikom-cutover-prepared/android-updates.conf
echo ANDROID_ACTIVE_SITE_REFERENCE
grep -En 'android|update' /etc/nginx/sites-available/celikom-site-https || true
echo ANDROID_V95_PRIVATE_STAGE_READONLY_ACCEPTED
