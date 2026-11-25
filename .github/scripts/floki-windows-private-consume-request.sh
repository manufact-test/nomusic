#!/bin/bash
# Separate owner-authorized administrative job. Import signed data only.
# Never called by the draft-write job itself, never publish or modify a feed.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 ]]
tool=/usr/local/lib/celikom-windows-intake/windows-stable-private-consume.py
[[ -f "$tool" && ! -L "$tool" && "$(stat -c '%u:%a' "$tool")" == 0:644 ]]
/usr/bin/python3 "$tool"
enroll=/home/celops/.celikom-windows-intake-enrollment
if [[ -e "$enroll" || -L "$enroll" ]]; then
  [[ -f "$enroll" && ! -L "$enroll" && "$(stat -c '%U:%a' "$enroll")" == celops:600 ]]
  rm -- "$enroll"
  echo WINDOWS_INTAKE_ONE_TIME_ENROLLMENT_COPY_REMOVED
fi
echo CELIKOM_WINDOWS_PRIVATE_HANDOFF_ROOT_VERIFIED_NOT_PUBLISHED
