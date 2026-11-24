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
 unsafe=[n for n in names if n.startswith("/") or ".." in pathlib.PurePosixPath(n).parts or any(x in n.lower() for x in (".env","secret","private","storage/audio","database"))]
 print("SERVER_ZIP_ENTRIES",len(names),"TOP",sorted({n.split("/")[0] for n in names})[:30])
 print("UNSAFE_NAMES",unsafe[:10])
 if unsafe: raise SystemExit("SERVER_PACKAGE_CONTAINS_PRIVATE_PATH_NAMES")
 matches=missing=changed=0
 for n in names:
  if not (stage/n).is_file(): missing+=1; continue
  a=hashlib.sha256(z.read(n)).hexdigest()
  b=hashlib.sha256((stage/n).read_bytes()).hexdigest()
  if a==b: matches+=1
  else: changed+=1
 print("STAGING_COMPARE_MATCH",matches,"MISSING",missing,"CHANGED",changed)
 print("SAMPLE_PATHS",names[:25])
PY
echo CELIKOM_PRIVATE_SERVER_PACKAGE_AUDIT_OK
