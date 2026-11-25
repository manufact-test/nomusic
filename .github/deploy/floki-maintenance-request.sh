#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Final infrastructure health and mirror check; no DB, config or release writes.
systemctl is-enabled celikom-mirror-sync.timer
systemctl is-active celikom-mirror-sync.timer forgejo nginx php8.3-fpm celikom-ci-runner.service certbot.timer
systemctl show celikom-mirror-sync.timer -p LastTriggerUSec -p NextElapseUSecRealtime
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus
journalctl -u celikom-mirror-sync.service --since '8 hours ago' --no-pager -o cat | grep -E 'VERIFIED_REFS=|CELIKOM_MIRROR_SYNC_OK' | tail -n 8
# Catch up the existing one-way repository mirror; no changes to GitHub.
systemctl start celikom-mirror-sync.service
runuser -u celikom-mirror -- bash -c '
set -euo pipefail
S=/home/celikom-mirror/.ssh
R=/home/celikom-mirror/github-mirror.git
GH="ssh -i $S/github-readonly -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/known_hosts -o BatchMode=yes"
FG="ssh -i $S/forgejo-write -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/forgejo_known_hosts -o BatchMode=yes"
for branch in main experiment/android-a1-metrica-init-state-observer-arm13-20261112; do
 ref=refs/heads/$branch
 gh=$(GIT_SSH_COMMAND="$GH" git ls-remote git@github.com:manufact-test/nomusic.git "$ref" | awk "{print \$1}")
 local=$(git --git-dir="$R" rev-parse "$ref")
 fj=$(GIT_SSH_COMMAND="$FG" git ls-remote git@127.0.0.1:celadmin/nomusic.git "$ref" | awk "{print \$1}")
 [[ "$gh" =~ ^[0-9a-f]{40}$ && "$gh" == "$local" && "$local" == "$fj" ]]
 printf "THREE_WAY_MIRROR_MATCH %s %s\n" "$branch" "$gh"
done
'
journalctl -u celikom-mirror-sync.service -n 20 --no-pager -o cat | grep -E 'VERIFIED_REFS=|CELIKOM_MIRROR_SYNC_OK' | tail -n 4
python3 - <<'PY'
import pathlib,hashlib,stat,json,datetime
p=pathlib.Path('/srv/celikom-releases/private/backend/5745e10c3a02917964e6aa433e59b24f4e684f34/celikom-server-0.4.57.zip')
s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==1136102
with p.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()=='15ad1af4be74a29d0ab182ac966755b4aac60e8995adba68f146d4827900526d'
root=pathlib.Path('/srv/celikom-releases/windows/stable')
assert root.joinpath('current').readlink()==pathlib.Path('versions/0.24.55')
m=json.loads(root.joinpath('current/manifest.json').read_bytes())
assert m['version']=='0.24.55' and m['sequence']==2
assert datetime.datetime.fromisoformat(m['expiresAt'].replace('Z','+00:00'))>datetime.datetime.now(datetime.timezone.utc)
print('WINDOWS_STAGED_MANIFEST_EXPIRY',m['expiresAt'])
apk=pathlib.Path('/srv/celikom-releases/private/android-build-inputs/CELIKOM-0.3.22-install.apk')
assert stat.S_IMODE(apk.lstat().st_mode)==0o600 and apk.lstat().st_uid==0 and apk.stat().st_size==8587421
with apk.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()=='170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9'
print('PRIVATE_BACKEND_AND_ANDROID_BASELINE_OK')
PY
openssl dgst -sha256 -verify /root/celikom-secrets/windows-stable-public.der -keyform DER -signature /srv/celikom-releases/windows/stable/current/manifest.json.sig /srv/celikom-releases/windows/stable/current/manifest.json
nginx -t
for item in 'api.celikom.com /api/v1/health 200' 'api.celikom.com /api/v1/config 200' 'api.celikom.com /admin/ 404' 'celikom.com / 401' 'celikom.com /admin/ 401' 'celikom.com /CELIKOM/Windows/Updates/stable/latest.json 401' 'celikom.com /updates/android/stable.json 401' 'celikom.com /downloads/windows/CELIKOM-Windows-0.24.55.exe 401' 'celikom.com /downloads/extension/celikom-extension-0.4.73.zip 401'; do
  read -r host route expected <<< "$item"
  actual=$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' "https://$host$route")
  printf 'ROUTE %s%s %s\n' "$host" "$route" "$actual"
  [[ "$actual" == "$expected" ]]
done
echo CELIKOM_MIGRATION_MORNING_INFRA_AUDIT_OK
