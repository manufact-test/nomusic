#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
BASE=/srv/celikom/migration/sites-20261124
python3 - "$BASE" <<'PY'
import json,pathlib,sys,hashlib
base=pathlib.Path(sys.argv[1])
for sub in ("android-public","android-private","api-public"):
 root=base/sub
 if not root.exists(): continue
 print("TREE",sub)
 for p in sorted(root.rglob("stable.json")):
  try: o=json.loads(p.read_text())
  except Exception: continue
  url=o.get("apkUrl","")
  name=url.split("/")[-1] if isinstance(url,str) else ""
  print("MANIFEST",p.relative_to(root),"bytes",p.stat().st_size,"version",o.get("versionName"),"code",o.get("versionCode"),"enabled",o.get("enabled"),"channel",o.get("channel"),"package",o.get("packageName"),"signer",o.get("signerSha256"),"size",o.get("sizeBytes"),"apk",name)
  for m in root.rglob(name) if name else []:
   b=m.read_bytes()
   print("APK",m.relative_to(root),"bytes",len(b),"sha256",hashlib.sha256(b).hexdigest())
PY
echo CELIKOM_ALL_ANDROID_MANIFESTS_AUDITED
