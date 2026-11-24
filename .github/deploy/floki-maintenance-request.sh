#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only verification of update manifest readiness, mirror timer and prior cutover cleanup.
root=/srv/celikom-releases/windows/stable
[[ "$(readlink "$root/current")" == versions/0.24.55 ]]
manifest="$root/current/manifest.json"
python3 - "$manifest" <<'PY'
import json,datetime,sys
v=json.load(open(sys.argv[1]))
assert v["version"]=="0.24.55" and v["sequence"]==2
assert v["packageUrl"]=="https://celikom.com/CELIKOM/Windows/Updates/stable/0.24.55/CELIKOM-Windows-0.24.55.exe"
expiry=datetime.datetime.fromisoformat(v["expiresAt"].replace("Z","+00:00"))
now=datetime.datetime.now(datetime.timezone.utc)
print("WINDOWS_MANIFEST_EXPIRY",expiry.isoformat(),"valid",expiry>now)
assert expiry>now
PY
openssl dgst -sha256 -verify /root/celikom-secrets/windows-stable-public.der -keyform DER -signature "$root/current/manifest.json.sig" "$manifest"
echo WINDOWS_STAGED_FEED_READY
echo '=== Existing mirror ==='
systemctl is-enabled celikom-mirror-sync.timer
systemctl is-active celikom-mirror-sync.timer
systemctl show celikom-mirror-sync.timer -p LastTriggerUSec -p NextElapseUSecRealtime
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus
journalctl -u celikom-mirror-sync.service --since '2 hours ago' --no-pager -o cat | grep -E 'VERIFIED_REFS=|CELIKOM_MIRROR_SYNC_OK|Finished' | tail -n 12 || true
runuser -u celikom-mirror -- git --git-dir=/home/celikom-mirror/github-mirror.git rev-parse refs/heads/main
echo '=== Cutover isolation ==='
test ! -e /etc/nginx/conf.d/celikom-cutover-probe.conf
test ! -e /usr/local/sbin/celikom-cutover-receive
test ! -e /etc/sudoers.d/celikom-cutover-receive
nginx -t
for path in /api/v1/health /api/v1/config /admin/; do
  printf 'PUBLIC_API %s ' "$path"
  curl -sS --max-time 15 -o /dev/null -w '%{http_code}\n' "https://api.celikom.com$path"
done
for path in / /admin/ /CELIKOM/Windows/Updates/stable/latest.json /updates/android/stable.json; do
  printf 'PUBLIC_SITE %s ' "$path"
  curl -sS --max-time 15 -o /dev/null -w '%{http_code}\n' "https://celikom.com$path"
done
echo CELIKOM_MIGRATION_READINESS_AUDIT_OK
