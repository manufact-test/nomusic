#!/bin/bash
set -Eeuo pipefail
echo '=== RELEASE DIRECTORY AUDIT ==='
for d in /root /root/celikom-release-import /root/celikom-secrets /srv /srv/celikom /srv/celikom/releases /srv/celikom/releases/windows /srv/celikom/releases/windows/stable; do
  stat -c '%n %F uid=%u gid=%g mode=%a' "$d"
done
echo '=== VERIFIED INPUTS ==='
sha256sum /root/celikom-release-import/windows-02455/0.24.55/CELIKOM-Windows-0.24.55.exe /srv/celikom/releases/private/extension/celikom-extension-0.4.73.zip
echo '=== API ROUTES ==='
for url in https://api.celikom.com/api/v1/health https://api.celikom.com/admin/login https://celikom.com/; do
  printf '%s ' "$url"; curl --max-time 10 -sS -o /dev/null -w '%{http_code}\n' "$url"
done
echo FLOKI_ADMIN_ACCESS_VERIFIED
