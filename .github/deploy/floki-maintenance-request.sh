#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
A=/srv/celikom/migration/sites-20261124/android-private
python3 - "$A" <<'PY'
import json,pathlib,sys,hashlib
root=pathlib.Path(sys.argv[1])
for p in sorted(root.rglob("stable.json")):
    try: o=json.loads(p.read_text())
    except Exception: continue
    print("MANIFEST",p.relative_to(root),"bytes",p.stat().st_size)
    print(" version",o.get("versionName"),"code",o.get("versionCode"),"enabled",o.get("enabled"),"channel",o.get("channel"))
    print(" package",o.get("packageName"),"signer",o.get("signerSha256"),"size",o.get("sizeBytes"))
    url=o.get("apkUrl","")
    name=url.split("/")[-1] if isinstance(url,str) else ""
    print(" apk",name)
    matches=list(root.rglob(name)) if name else []
    for m in matches:
        b=m.read_bytes()
        print(" match",m.relative_to(root),"size",len(b),"sha256",hashlib.sha256(b).hexdigest())
PY
echo CELIKOM_ANDROID_UPDATE_MANIFESTS_ENUMERATED
