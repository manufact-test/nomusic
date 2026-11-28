#!/bin/bash
# W195 one-time repair: publish the exact signed 0.24.62 bootstrap/rollback
# image required by already-installed 0.24.62 clients. Never change latest.
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[[ "$(id -u)" == 0 ]] || { echo W195_ROOT_REQUIRED; exit 1; }

ROOT=/srv/celikom-releases/windows/stable
CUSTOMER=/srv/celikom-releases/public/windows-customer-stable
VERSION=0.24.62
SOURCE="$ROOT/versions/$VERSION"
DEST="$CUSTOMER/versions/$VERSION"
PIN=/root/celikom-secrets/windows-stable-public.der
TOOLS=/root/celikom-release-tools
EXPECTED_PACKAGE_SHA=5daad26eefeacca7b3f1a08c7d6fe0c07bc50e73ae9d601b5a7d71f4be1f37a9
EXPECTED_PACKAGE_SIZE=85156133
EXPECTED_LATEST_SHA=3315b43e5af8c789f77fe643478b27f466bb4d5c76a591d34ce15143e2b2515f

[[ "$(sha256sum "$PIN" | cut -d' ' -f1)" == 46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95 ]] || { echo W195_PIN_PREFLIGHT_FAILED; exit 1; }
[[ "$(git hash-object "$TOOLS/windows-stable-existing-latest.mjs")" == bb4d19672d45bdd0393497c3b33280308d67ef32 ]] || { echo W195_TRUSTED_VERIFIER_PREFLIGHT_FAILED; exit 1; }
[[ "$(readlink "$ROOT/current")" == versions/0.24.63 ]] || { echo W195_LOCAL_CURRENT_NOT_02463; exit 1; }
python3 - "$SOURCE" "$EXPECTED_PACKAGE_SIZE" <<'PY'
import stat,sys
from pathlib import Path
d=Path(sys.argv[1])
s=d.lstat()
assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022
for name in ("manifest.json","manifest.json.sig","CELIKOM-Windows-0.24.62.exe"):
    p=d/name
    x=p.lstat()
    assert stat.S_ISREG(x.st_mode) and x.st_uid==0 and not x.st_mode&0o022
assert (d/"CELIKOM-Windows-0.24.62.exe").stat().st_size==int(sys.argv[2])
print("W195_LOCAL_02462_FILES_ROOT_OWNED_AND_IMMUTABLE")
PY
printf '%s  %s\n' "$EXPECTED_PACKAGE_SHA" "$SOURCE/CELIKOM-Windows-0.24.62.exe" | sha256sum -c
python3 - "$SOURCE/manifest.json" "$EXPECTED_PACKAGE_SHA" "$EXPECTED_PACKAGE_SIZE" <<'PY'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8"))
assert (m["version"],m["sequence"],m["sha256"],m["packageSize"]) == (
    "0.24.62",9,sys.argv[2],int(sys.argv[3]))
assert m["packageUrl"] == "https://celikom.com/CELIKOM/Windows/Updates/stable/0.24.62/CELIKOM-Windows-0.24.62.exe"
assert m["schema"]==2 and m["channel"]=="stable" and m["publisher"]=="CELIKOM"
print("W195_LOCAL_02462_SIGNED_RELEASE_IDENTITY_OK")
PY

export CELIKOM_STABLE_ORIGIN=https://celikom.com
export CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64=$(base64 -w0 "$PIN")
node "$TOOLS/windows-stable-existing-latest.mjs" "$SOURCE/manifest.json" "$SOURCE/manifest.json.sig"

for d in "$CUSTOMER" "$CUSTOMER/versions"; do
  [[ -d "$d" && ! -L "$d" && "$(stat -c '%u' "$d")" == 0 ]] || { echo W195_CUSTOMER_PUBLIC_ROOT_INVALID; exit 1; }
done
[[ "$(stat -c '%a' "$CUSTOMER/versions")" == 755 ]] || { echo W195_CUSTOMER_VERSIONS_MODE_INVALID; exit 1; }

tmp=$(mktemp -d /root/celikom-w195-02462-bootstrap.XXXXXXXX)
cleanup() { rm -rf -- "$tmp"; }
trap cleanup EXIT
BASE=https://celikom.com/CELIKOM/Windows/Updates/stable

# Pin the already-approved 0.24.63 latest pair before the narrow copy.
curl --proto '=https' -fsS --max-time 30 "$BASE/latest.json" -o "$tmp/latest.before.json"
curl --proto '=https' -fsS --max-time 30 "$BASE/latest.json.sig" -o "$tmp/latest.before.sig"
node "$TOOLS/windows-stable-existing-latest.mjs" "$tmp/latest.before.json" "$tmp/latest.before.sig"
python3 - "$tmp/latest.before.json" "$EXPECTED_LATEST_SHA" <<'PY'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8"))
assert (m["version"],m["sequence"],m["sha256"]) == ("0.24.63",10,sys.argv[2])
print("W195_CUSTOMER_LATEST_02463_PINNED_BEFORE_BOOTSTRAP_COPY")
PY

# Publish only the old immutable bootstrap/rollback files. Never alter latest,
# latest.sig, accepted.json, stable.exe, owner downloads, Nginx or API routes.
python3 - "$SOURCE" "$DEST" <<'PY'
import hashlib,os,shutil,stat,sys,tempfile
from pathlib import Path
src,dst=Path(sys.argv[1]),Path(sys.argv[2])
if dst.exists() or dst.is_symlink():
    s=dst.lstat()
    assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022
else:
    os.mkdir(dst,0o755)
    os.chown(dst,0,0)
    os.chmod(dst,0o755)
for name in ("manifest.json","manifest.json.sig","CELIKOM-Windows-0.24.62.exe"):
    source=src/name
    ss=source.lstat()
    assert stat.S_ISREG(ss.st_mode) and ss.st_uid==0 and not ss.st_mode&0o022
    h=hashlib.sha256()
    with source.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    expected=h.hexdigest()
    target=dst/name
    if target.exists() or target.is_symlink():
        ts=target.lstat()
        assert stat.S_ISREG(ts.st_mode) and ts.st_uid==0 and not ts.st_mode&0o022
        assert ts.st_size==ss.st_size
        th=hashlib.sha256()
        with target.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""): th.update(chunk)
        assert th.hexdigest()==expected, "W195_PUBLIC_IMMUTABLE_CONFLICT_"+name
        print("W195_BOOTSTRAP_FILE_ALREADY_IDENTICAL",name,ss.st_size,expected)
        continue
    fd,tmp=tempfile.mkstemp(prefix=".w195-02462-",dir=dst)
    try:
        with os.fdopen(fd,"wb") as out,source.open("rb") as inp:
            shutil.copyfileobj(inp,out,1024*1024)
            out.flush();os.fsync(out.fileno())
        os.chown(tmp,0,0);os.chmod(tmp,0o644)
        with open(tmp,"rb") as check:
            assert hashlib.file_digest(check,"sha256").hexdigest()==expected
        os.link(tmp,target)
        print("W195_BOOTSTRAP_FILE_PUBLISHED",name,ss.st_size,expected)
    finally:
        if os.path.lexists(tmp): os.unlink(tmp)
PY

# Confirm the three exact files are now reachable over the updater's public HTTPS route.
curl --proto '=https' -fsS --max-time 30 "$BASE/0.24.62/manifest.json" -o "$tmp/public-manifest.json"
curl --proto '=https' -fsS --max-time 30 "$BASE/0.24.62/manifest.json.sig" -o "$tmp/public-manifest.json.sig"
cmp "$SOURCE/manifest.json" "$tmp/public-manifest.json"
cmp "$SOURCE/manifest.json.sig" "$tmp/public-manifest.json.sig"
node "$TOOLS/windows-stable-existing-latest.mjs" "$tmp/public-manifest.json" "$tmp/public-manifest.json.sig"
curl --proto '=https' -fsS --max-time 180 --max-filesize 125000000 "$BASE/0.24.62/CELIKOM-Windows-0.24.62.exe" -o "$tmp/public-installer.exe"
[[ "$(stat -c '%s' "$tmp/public-installer.exe")" == "$EXPECTED_PACKAGE_SIZE" ]]
printf '%s  %s\n' "$EXPECTED_PACKAGE_SHA" "$tmp/public-installer.exe" | sha256sum -c

# Prove the current customer release and signature were not changed.
curl --proto '=https' -fsS --max-time 30 "$BASE/latest.json" -o "$tmp/latest.after.json"
curl --proto '=https' -fsS --max-time 30 "$BASE/latest.json.sig" -o "$tmp/latest.after.sig"
cmp "$tmp/latest.before.json" "$tmp/latest.after.json"
cmp "$tmp/latest.before.sig" "$tmp/latest.after.sig"
node "$TOOLS/windows-stable-existing-latest.mjs" "$tmp/latest.after.json" "$tmp/latest.after.sig"
python3 - "$tmp/latest.after.json" "$EXPECTED_LATEST_SHA" "$CUSTOMER/accepted.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1],encoding="utf-8"))
a=json.load(open(sys.argv[3],encoding="utf-8"))
assert (m["version"],m["sequence"],m["sha256"]) == ("0.24.63",10,sys.argv[2])
assert a=={"version":"0.24.63","sequence":10,"sha256":sys.argv[2],"https_verified":True}
print("W195_CUSTOMER_LATEST_02463_UNCHANGED_AND_ACCEPTED")
PY
echo W195_PUBLIC_02462_BOOTSTRAP_AND_ROLLBACK_HTTPS_VERIFIED_LATEST_02463_UNCHANGED
