#!/bin/bash
set -Eeuo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Only the public SSH host key is requested, not the enrollment secret or
# the private server key. The established pinned maintenance SSH authenticates
# this response, independently of the new dedicated data-only credential.
pub=/etc/ssh/ssh_host_ed25519_key.pub
test -f "$pub" && test ! -L "$pub"
test "$(stat -c '%u' "$pub")" = 0
read -r kind key comment < "$pub"
[[ "$kind" = ssh-ed25519 && "$key" =~ ^[A-Za-z0-9+/=]+$ ]]
fingerprint=$(ssh-keygen -lf "$pub" -E sha256 | awk '{print $2}')
test "$fingerprint" = SHA256:eqVsJpDin/3W3QeDMzO1t0OOiZ03XQksrCkMgPrf9X4
printf 'CELIKOM_VERIFIED_PUBLIC_HOST_PIN 95.133.160.111 %s %s\n' "$kind" "$key"
printf 'CELIKOM_VERIFIED_PUBLIC_HOST_FINGERPRINT %s\n' "$fingerprint"
echo WINDOWS_INTAKE_TRUSTED_PUBLIC_HOST_PIN_OK
