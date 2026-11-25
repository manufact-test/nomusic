#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only, no secrets or SQL rows in output.
root=/root/celikom-cutover-snapshot-zOYBzdmN/intake
for item in \
  'api 24f79abcbf40096161b2a57168bb31a447d5e35e88c9e3b729474b0ea6cc4ec9' \
  'cms 19d592658438d55703c82691f42aec9b87b1fe53fd02f805c644f6107490552d'; do
  read -r name expected <<< "$item"
  path="$root/$name.sql.gz"
  test -f "$path" && test ! -L "$path"
  digest=$(sha256sum "$path" | cut -d' ' -f1)
  test "$digest" = "$expected"
  gzip -t "$path"
  echo "FINAL_FROZEN_SQL_PRESENT_AND_INTEGRITY_OK" "$name" "$(stat -c %s "$path")"
done
# Failed additive archive must not leave loose SQL/config secrets.
dir=/srv/celikom/migration/final-delta-20261125
if test -d "$dir"; then
  find "$dir" -maxdepth 3 -type f -printf 'FAILED_BACKUP_RESIDUAL_FILENAME %P %s\n'
fi
test ! -f /srv/celikom/migration/backups/celikom-final-delta-20261125.tar.gpg
echo POSTCUTOVER_ENCRYPTED_DELTA_NOT_COMPLETE
nginx -t
for endpoint in /api/v1/health /api/v1/config /api/v1/auth/me /api/v1/entitlement; do
  status=$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' "https://api.celikom.com$endpoint")
  echo "PUBLIC_API_STATUS" "$endpoint" "$status"
done
tmp=$(mktemp)
trap 'rm -f -- "$tmp"' EXIT
status=$(curl -sS --max-time 15 -o "$tmp" -w '%{http_code}' \
  -X POST -H 'Content-Type: application/json' -d '{}' \
  https://api.celikom.com/api/v1/auth/activate)
test "$status" = 401
python3 - "$tmp" <<'PY'
import json,sys
data=json.load(open(sys.argv[1]))
assert isinstance(data,dict) and isinstance(data.get('error'),str)
print('PUBLIC_API_AUTH_ACTIVATE_POST_REACHABLE_WITH_JSON_401')
PY
echo CELIKOM_POSTCUTOVER_SQL_AND_API_AUTH_READONLY_ACCEPTANCE_COMPLETE
