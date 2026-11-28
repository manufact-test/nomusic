#!/bin/bash
# CELIKOM_WINDOWS_STABLE_APPROVAL_RUN=46084804919
# One-time, approved Windows-only public stable route cutover.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 ]]
ROOT=/srv/celikom-releases/windows/stable
OWNER=/srv/celikom-releases/owner-downloads
PIN=/root/celikom-secrets/windows-stable-public.der
TOOLS=/root/celikom-release-tools
LIB=/usr/local/lib/celikom-windows-intake
PREP=/root/celikom-cutover-prepared
VERSION=0.24.63
SEQUENCE=10
PACKAGE_SHA=3315b43e5af8c789f77fe643478b27f466bb4d5c76a591d34ce15143e2b2515f

[[ "$(sha256sum "$PIN" | cut -d' ' -f1)" == 46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95 ]]
[[ "$(git hash-object "$LIB/floki-windows-signed-root-consumer.py")" == 83c93178a07d9811286163d99ae0c23946013a7c ]]
[[ "$(git hash-object "$TOOLS/windows-stable-existing-latest.mjs")" == bb4d19672d45bdd0393497c3b33280308d67ef32 ]]
systemctl is-active --quiet celikom-windows-signed-owner.timer

python3 - <<'PY'
import importlib.util
from pathlib import Path
p=Path('/usr/local/lib/celikom-windows-intake/floki-windows-signed-root-consumer.py')
s=importlib.util.spec_from_file_location('celikom_root_consumer',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
pending=m.list_pending()
assert len(pending)<=1, 'UNEXPECTED_PENDING_WINDOWS_RELEASES'
if pending:
    seq,version,archive_sha,path,ino,dev,size=pending[0]
    assert (version,seq)==('0.24.63',10), 'UNEXPECTED_PENDING_WINDOWS_RELEASE_ID'
    print('W194_EXACT_02463_SIGNED_TRANSFER_PENDING',archive_sha,size)
else:
    print('W194_SIGNED_TRANSFER_ALREADY_CONSUMED')
PY

systemctl start celikom-windows-signed-owner.service
[[ "$(readlink "$ROOT/current")" == versions/0.24.63 ]]
[[ -f "$ROOT/current/manifest.json" && ! -L "$ROOT/current/manifest.json" ]]
[[ -f "$ROOT/current/manifest.json.sig" && ! -L "$ROOT/current/manifest.json.sig" ]]
[[ -f "$ROOT/current/CELIKOM-Windows-0.24.63.exe" && ! -L "$ROOT/current/CELIKOM-Windows-0.24.63.exe" ]]
[[ -f "$ROOT/owner-verified.json" && ! -L "$ROOT/owner-verified.json" ]]
export CELIKOM_STABLE_ORIGIN=https://celikom.com
export CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64=$(base64 -w0 "$PIN")
node "$TOOLS/windows-stable-existing-latest.mjs" "$ROOT/current/manifest.json" "$ROOT/current/manifest.json.sig"
unset CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
python3 - "$ROOT" "$OWNER" "$PACKAGE_SHA" <<'PY'
import hashlib,json,stat,sys
from pathlib import Path
root,owner=Path(sys.argv[1]),Path(sys.argv[2]); expected=sys.argv[3]
m=json.loads((root/'current/manifest.json').read_bytes())
r=json.loads((root/'owner-verified.json').read_bytes())
assert (m['version'],m['sequence'],m['sha256'])==('0.24.63',10,expected)
assert r=={'version':'0.24.63','sequence':10,'sha256':expected,'https_verified':True}
exe=root/'current/CELIKOM-Windows-0.24.63.exe'
s=exe.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022 and s.st_size==m['packageSize']
h=hashlib.sha256()
with exe.open('rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
assert h.hexdigest()==expected
latest=owner/'CELIKOM-Windows-latest.exe'
assert latest.is_file() and not latest.is_symlink()
assert latest.stat().st_size==m['packageSize']
h=hashlib.sha256()
with latest.open('rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
assert h.hexdigest()==expected
for old in ('0.24.55','0.24.62'):
    d=root/'versions'/old
    if d.exists():
        assert d.is_dir() and not d.is_symlink()
        assert (d/'manifest.json').is_file() and (d/'manifest.json.sig').is_file()
        print('W194_OLDER_IMMUTABLE_VERSION_PRESERVED',old)
print('W194_LOCAL_SIGNED_CURRENT_AND_OWNER_RECEIPT_OK',m['packageSize'],expected)
PY

getent ahostsv4 celikom.com | awk '$1=="95.133.160.111"{ok=1} END{exit !ok}' || {
  echo W194_PUBLIC_DNS_NO_LONGER_POINTS_TO_FLOKI; exit 1;
}

SITE_LINK=/etc/nginx/sites-enabled/celikom-site-https
[[ -L "$SITE_LINK" ]]
SITE=$(readlink -f "$SITE_LINK")
[[ "$SITE" == /etc/nginx/sites-available/* && -f "$SITE" && ! -L "$SITE" ]]
SNIPPET="$PREP/windows-stable-locations.conf"
[[ "$(stat -c '%u:%a' "$SNIPPET")" == 0:600 ]]
marker='    # END CELIKOM OWNER DOWNLOADS'
[[ "$(grep -Fc "$marker" "$SITE")" == 1 ]]
if grep -Fq '/CELIKOM/Windows/Updates/stable/latest.json' "$SITE"; then
  echo W194_STABLE_ROUTE_ALREADY_EXISTS_REVIEW_REQUIRED; exit 1
fi
[[ "$(grep -Fc 'location ' "$SNIPPET")" == 4 ]]
grep -Fq 'alias /srv/celikom-releases/windows/stable/current/manifest.json;' "$SNIPPET"
grep -Fq 'alias /srv/celikom-releases/windows/stable/current/manifest.json.sig;' "$SNIPPET"
grep -Fq 'alias /srv/celikom-releases/windows/stable/versions/$cwv/$cwm;' "$SNIPPET"
grep -Fq 'alias /srv/celikom-releases/windows/stable/versions/$cwe/CELIKOM-Windows-$cwe.exe;' "$SNIPPET"
! grep -Eq 'auth_basic|proxy_pass|include ' "$SNIPPET"

CUTOVER_BACKUP="$PREP/site-https.pre-02463-approved.conf"
[[ ! -e "$CUTOVER_BACKUP" && ! -L "$CUTOVER_BACKUP" ]]
cp -a "$SITE" "$CUTOVER_BACKUP"
changed=0
verified=0
tmp=$(mktemp -d /root/celikom-windows-ota-verify.XXXXXXXX)
cleanup() {
  rc=$?
  if [[ "$changed" == 1 && "$verified" != 1 ]]; then
    cp -a "$CUTOVER_BACKUP" "$SITE"
    nginx -t && systemctl reload nginx || true
    echo W194_NGINX_ROUTE_CHANGE_ROLLED_BACK
  fi
  rm -rf -- "$tmp"
  exit "$rc"
}
trap cleanup EXIT

python3 - "$SITE" "$SNIPPET" <<'PY'
import os,pathlib,stat,sys,tempfile
p=pathlib.Path(sys.argv[1]); snippet=pathlib.Path(sys.argv[2]).read_text()
s=p.read_text()
marker='    # END CELIKOM OWNER DOWNLOADS'
assert s.count(marker)==1 and '/CELIKOM/Windows/Updates/stable/latest.json' not in s
assert snippet.count('location ')==4
out=s.replace(marker,snippet.rstrip()+'\n\n'+marker,1)
st=p.stat()
fd,t=tempfile.mkstemp(prefix='.celikom-windows-stable-',dir=p.parent)
try:
    with os.fdopen(fd,'w') as f:
        f.write(out);f.flush();os.fsync(f.fileno())
    os.chown(t,st.st_uid,st.st_gid);os.chmod(t,stat.S_IMODE(st.st_mode))
    os.replace(t,p)
finally:
    if os.path.exists(t):os.unlink(t)
PY
changed=1
nginx -t
systemctl reload nginx

BASE=https://celikom.com/CELIKOM/Windows/Updates/stable
curl --proto '=https' -fsS --max-time 30 "$BASE/latest.json" -o "$tmp/latest.json"
curl --proto '=https' -fsS --max-time 30 "$BASE/latest.json.sig" -o "$tmp/latest.json.sig"
cmp "$tmp/latest.json" "$ROOT/current/manifest.json"
cmp "$tmp/latest.json.sig" "$ROOT/current/manifest.json.sig"
curl --proto '=https' -fsS --max-time 30 "$BASE/0.24.63/manifest.json" -o "$tmp/versioned-manifest.json"
curl --proto '=https' -fsS --max-time 30 "$BASE/0.24.63/manifest.json.sig" -o "$tmp/versioned-manifest.json.sig"
cmp "$tmp/versioned-manifest.json" "$ROOT/versions/0.24.63/manifest.json"
cmp "$tmp/versioned-manifest.json.sig" "$ROOT/versions/0.24.63/manifest.json.sig"
export CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64=$(base64 -w0 "$PIN")
node "$TOOLS/windows-stable-existing-latest.mjs" "$tmp/latest.json" "$tmp/latest.json.sig"
unset CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
curl --proto '=https' -fsS --max-time 180 --max-filesize 125000000 "$BASE/0.24.63/CELIKOM-Windows-0.24.63.exe" -o "$tmp/public.exe"
[[ "$(stat -c '%s' "$tmp/public.exe")" == "$(stat -c '%s' "$ROOT/current/CELIKOM-Windows-0.24.63.exe")" ]]
printf '%s  %s\n' "$PACKAGE_SHA" "$tmp/public.exe" | sha256sum -c

for old in 0.24.55 0.24.62; do
  if [[ -d "$ROOT/versions/$old" ]]; then
    curl --proto '=https' -fsSI --max-time 20 "$BASE/$old/manifest.json" >/dev/null
    curl --proto '=https' -fsSI --max-time 20 "$BASE/$old/manifest.json.sig" >/dev/null
  fi
done

python3 - "$tmp/latest.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
assert (m['version'],m['sequence'],m['sha256'])==('0.24.63',10,'3315b43e5af8c789f77fe643478b27f466bb4d5c76a591d34ce15143e2b2515f')
assert m['packageUrl']=='https://celikom.com/CELIKOM/Windows/Updates/stable/0.24.63/CELIKOM-Windows-0.24.63.exe'
print('W194_PUBLIC_STABLE_02463_SEQUENCE10_CONFIRMED')
PY
verified=1
echo W194_WINDOWS_02463_APPROVED_STABLE_OTA_ROUTE_CUTOVER_OK
