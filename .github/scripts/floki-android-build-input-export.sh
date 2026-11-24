#!/bin/bash
# Fixed, read-only export of the pinned CELIKOM Android build baseline.
# Invoked only by the restricted celikom-deploy SSH gateway; binary stdout only.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ $(id -u) == 0 && $# == 0 ]] || exit 64
FILE=/srv/celikom-releases/private/android-build-inputs/CELIKOM-0.3.22-install.apk
[[ -f "$FILE" && ! -L "$FILE" ]]
[[ $(stat -c '%u:%a:%s' "$FILE") == 0:600:8587421 ]]
[[ $(sha256sum "$FILE" | cut -d' ' -f1) == 170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9 ]]
exec cat -- "$FILE"
