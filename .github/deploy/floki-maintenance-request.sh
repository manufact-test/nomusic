#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
SRC=/srv/celikom/migration/sites-20261124/android-private/android-updates
DST=/srv/celikom-releases/private/android-updates
NAME=93-5ceb9db20d47390e88cd316c3f74c1928534b35bc54e316f5b841f49b951ff6a.apk
python3 - "$SRC/stable.json" "$SRC/releases/$NAME" <<'PY'
import json,pathlib,hashlib,sys
m=json.loads(pathlib.Path(sys.argv[1]).read_text())
expected={"schemaVersion":1,"enabled":True,"channel":"stable","packageName":"pro.celikom.nativeprobe","versionCode":93,"versionName":"0.3.92","signerSha256":"67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f","sizeBytes":8845385,"minSdk":28}
for k,v in expected.items():
 if m.get(k)!=v: raise SystemExit("ANDROID_STABLE_MANIFEST_MISMATCH_"+k)
if m.get("apkUrl","").split("/")[-1]!=pathlib.Path(sys.argv[2]).name: raise SystemExit("ANDROID_STABLE_ASSET_NAME_MISMATCH")
b=pathlib.Path(sys.argv[2]).read_bytes()
if len(b)!=expected["sizeBytes"] or hashlib.sha256(b).hexdigest()!=m.get("apkSha256"): raise SystemExit("ANDROID_STABLE_APK_HASH_MISMATCH")
print("ANDROID_STABLE_SOURCE_VERIFIED",len(b),hashlib.sha256(b).hexdigest())
print("ANDROID_STABLE_MANIFEST_SHA256",hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
install -d -o root -g root -m 700 "$DST" "$DST/releases"
if [[ -e "$DST/stable.json" ]]; then cmp "$SRC/stable.json" "$DST/stable.json"; else install -o root -g root -m 600 "$SRC/stable.json" "$DST/stable.json"; fi
if [[ -e "$DST/releases/$NAME" ]]; then cmp "$SRC/releases/$NAME" "$DST/releases/$NAME"; else install -o root -g root -m 600 "$SRC/releases/$NAME" "$DST/releases/$NAME"; fi
cmp "$SRC/stable.json" "$DST/stable.json"
cmp "$SRC/releases/$NAME" "$DST/releases/$NAME"
test "$(stat -c %i "$SRC/releases/$NAME")" != "$(stat -c %i "$DST/releases/$NAME")"
sha256sum "$DST/stable.json" "$DST/releases/$NAME"
stat -c '%n mode=%a owner=%U:%G size=%s' "$DST" "$DST/stable.json" "$DST/releases" "$DST/releases/$NAME"
echo CELIKOM_ANDROID_STABLE_PRIVATE_STAGE_OK
