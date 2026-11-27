#!/bin/bash
# Called ONLY after a recorded GitHub windows-stable-production approval.
# The workflow prepends a short-lived GitHub artifact download URL. No token
# or signing key is sent to Floki. All installed verification tools remain intact.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 ]]
: "${ARTIFACT_URL:?missing exact approved artifact URL}"
ROOT=/srv/celikom-releases/windows/stable
PUBLIC=/srv/celikom-releases/public/windows-customer-stable
PIN=/root/celikom-secrets/windows-stable-public.der
LIB=/usr/local/lib/celikom-windows-intake
TOOLS=/root/celikom-release-tools
VERSION=0.24.63
SEQUENCE=10
HASH=3315b43e5af8c789f77fe643478b27f466bb4d5c76a591d34ce15143e2b2515f
ARCHIVE=9d7074fdd0610ebb7f4f00645f882271d595ac13efa05146141c6d2e8cc653b1
BASE=https://celikom.com/CELIKOM/Windows/Updates/stable
[[ "$(sha256sum "$PIN" | cut -d' ' -f1)" == 46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95 ]]
[[ "$(git hash-object "$LIB/floki-windows-signed-root-consumer.py")" == 83c93178a07d9811286163d99ae0c23946013a7c ]]
[[ "$(git hash-object "$LIB/customer-stable-consumer.py")" == e705c71c94b02727c7eb81de791b061075306b6b ]]
[[ "$(git hash-object "$TOOLS/windows-stable-existing-latest.mjs")" == bb4d19672d45bdd0393497c3b33280308d67ef32 ]]
systemctl is-active --quiet celikom-windows-customer-stable.timer
tmp=$(mktemp -d /root/celikom-win-02463-promotion.XXXXXXXX)
trap 'rm -rf -- "$tmp"' EXIT
# Start the expiring artifact download immediately; then verify the exact outer archive.
curl --proto '=https' --fail --silent --max-time 180 --max-filesize 130000000 -o "$tmp/artifact.zip" "$ARTIFACT_URL"
unset ARTIFACT_URL
printf '%s  %s\n' "$ARCHIVE" "$tmp/artifact.zip" | sha256sum -c
# Do not route public traffic to the private current pointer. The existing
# customer publisher preserves the older accepted version and public URLs.
curl --proto '=https' -fsS --max-time 30 --max-filesize 16384 "$BASE/latest.json" -o "$tmp/latest.json"
curl --proto '=https' -fsS --max-time 30 --max-filesize 80 "$BASE/latest.json.sig" -o "$tmp/latest.json.sig"
cmp "$tmp/latest.json" "$PUBLIC/latest.json"
cmp "$tmp/latest.json.sig" "$PUBLIC/latest.json.sig"
export CELIKOM_STABLE_ORIGIN=https://celikom.com
export CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64=$(base64 -w0 "$PIN")
node "$TOOLS/windows-stable-existing-latest.mjs" "$tmp/latest.json" "$tmp/latest.json.sig"
unset CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
python3 - "$tmp" "$HASH" <<'PY'
import json,sys,zipfile,shutil
from pathlib import Path
p=Path(sys.argv[1]); expected=sys.argv[2]
m=json.loads((p/'latest.json').read_bytes())
assert (m['version'],m['sequence'],m['sha256']) in (
    ('0.24.55',2,'f4c9a7881164ac7a9b5681d9f3568e5cbd3a9915c9e1da7b475caa20d3fb6487'),
    ('0.24.63',10,expected)), 'PUBLIC_FLOOR_CHANGED'
with zipfile.ZipFile(p/'artifact.zip') as z:
    assert z.namelist()==['CELIKOM-Windows-P256-transfer.zip'], 'ARTIFACT_LAYOUT'
    info=z.infolist()[0]
    assert 22<=info.file_size<=125100000
    with z.open(info) as src,(p/'transfer.zip').open('xb') as dst:
        shutil.copyfileobj(src,dst,1024*1024)
with zipfile.ZipFile(p/'transfer.zip') as z:
    info=z.getinfo('0.24.63/manifest.json')
    assert 100<=info.file_size<=16384
    m=json.loads(z.read(info))
    assert (m['version'],m['sequence'],m['sha256'])==('0.24.63',10,expected)
PY
# Reuse the installed root consumer and its existing lock, importer, pinned
# P-256 verifier, owner route checks and receipt. No new runner or permissions.
python3 - "$tmp/transfer.zip" "$HASH" <<'PY'
import fcntl,importlib.util,json,os,sys
from pathlib import Path
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
lib=Path('/usr/local/lib/celikom-windows-intake')
r=load('owner_consumer',lib/'floki-windows-signed-root-consumer.py')
c=load('customer_consumer',lib/'customer-stable-consumer.py')
v='0.24.63';seq=10;h=sys.argv[2];a={'version':v,'sequence':seq,'sha256':h,'owner_accepted':True}
r.verify_installed_tools()
fd=os.open(r.IMPORT_ROOT/'.windows-signed-spool.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
try:
    fcntl.flock(fd,fcntl.LOCK_EX)
    assert not r.list_pending(), 'UNEXPECTED_PENDING_OWNER_TRANSFER'
    assert os.readlink(r.ROOT/'current') in ('versions/0.24.62','versions/0.24.63'), 'LOCAL_FLOOR_CHANGED'
    r.independently_import(Path(sys.argv[1]),v,seq)
    r.publish_signed_root(v,seq)
    c.verify_signed(v,a)
    r.owner_copy(v)
    r.probe_website(v)
    r.record_verified_owner(v,seq)
finally:
    os.close(fd)
print('W194_EXACT_SIGNED_OWNER_RELEASE_READY_FOR_EXISTING_CUSTOMER_APPROVAL')
PY
