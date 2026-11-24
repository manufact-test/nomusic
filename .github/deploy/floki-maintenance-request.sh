#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
A=/srv/celikom/migration/sites-20261124/android-private
echo '=== Android updater files in copied private tree ==='
find "$A" -type f \( -name stable.json -o -name '*.apk' -o -name '*.sig' -o -name 'manifest*.json' \) -printf '%P %s bytes\n' | sort | tail -n 65
echo '=== Exact stable manifest metadata (no tokens or URLs) ==='
python3 - "$A" <<'PY'
import json,pathlib,sys,hashlib
root=pathlib.Path(sys.argv[1])
files=list(root.rglob("stable.json"))
for p in files:
    try:
        o=json.loads(p.read_text())
    except Exception:
        continue
    print("MANIFEST",p.relative_to(root))
    for k in ("schemaVersion","enabled","channel","packageName","versionCode","versionName","signerSha256","sizeBytes","minSdk"):
        print(k,repr(o.get(k)))
    url=o.get("apkUrl","")
    print("apkUrl_path",url.split("?",1)[0].split("/")[-1] if isinstance(url,str) else "INVALID")
    if isinstance(url,str):
        name=url.split("/")[-1]
        matches=list(root.rglob(name))
        for m in matches:
            h=hashlib.sha256(m.read_bytes()).hexdigest()
            print("APK_MATCH",m.relative_to(root),m.stat().st_size,h)
PY
echo '=== Android build-input baseline private copy ==='
f=/srv/celikom-releases/private/android-build-inputs/CELIKOM-0.3.22-install.apk
stat -c 'mode=%a owner=%U:%G size=%s' "$f"
sha256sum "$f"
echo CELIKOM_ANDROID_PRIVATE_INPUT_INVENTORY_OK
