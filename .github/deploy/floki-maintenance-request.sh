#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/ci-runner/runner/celikom-build-spool/d7537830c054a7878b080e21b9ea91e21e29bc56-45433182374-1
python3 - "$S" /srv/celikom/app/staging-20261122 <<'PY'
import pathlib,zipfile,hashlib,json,sys
spool=pathlib.Path(sys.argv[1]); stage=pathlib.Path(sys.argv[2])
receipt=json.loads((spool/"receipt.json").read_text())
print("RECEIPT_SHA",receipt.get("sha"),"RUN",receipt.get("runId"),"ATTEMPT",receipt.get("attempt"))
for p in spool.iterdir():
 if p.is_file(): print("SPOOL_FILE",p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
zpath=next(spool.glob("celikom-server-*.zip"))
with zipfile.ZipFile(zpath) as z:
 names=[n for n in z.namelist() if not n.endswith("/")]
 def unsafe(n):
  p=pathlib.PurePosixPath(n)
  low=n.lower()
  return (p.is_absolute() or ".." in p.parts or
    p.name==".env" or low.endswith((".pem",".p12",".pfx",".jks",".keystore",".key")) or
    "private-audio" in low or "storage/audio" in low or
    low.endswith((".sql.gz",".sqlite",".db")) or
    "/secrets/" in low)
 bad=[n for n in names if unsafe(n)]
 print("SERVER_ZIP_ENTRIES",len(names),"TOP",sorted({n.split("/")[0] for n in names})[:30])
 print("PRIVATE_PAYLOAD_NAMES",bad[:20])
 if bad: raise SystemExit("SERVER_PACKAGE_PRIVATE_PAYLOAD_PATH_FOUND")
 matches=missing=changed=0
 for n in names:
  target=stage/n
  if not target.is_file(): missing+=1; continue
  a=hashlib.sha256(z.read(n)).hexdigest()
  b=hashlib.sha256(target.read_bytes()).hexdigest()
  if a==b: matches+=1
  else: changed+=1
 print("STAGING_COMPARE_MATCH",matches,"MISSING",missing,"CHANGED",changed)
 print("SAMPLE_PATHS",names[:25])
PY
echo CELIKOM_PRIVATE_SERVER_PACKAGE_CONTENT_AUDIT_OK
