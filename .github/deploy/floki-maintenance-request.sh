#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/ci-runner/runner/celikom-build-spool/d7537830c054a7878b080e21b9ea91e21e29bc56-45433182374-1
python3 - "$S" /srv/celikom/app/staging-20261122 <<'PY'
import pathlib,zipfile,hashlib,sys
spool=pathlib.Path(sys.argv[1]); stage=pathlib.Path(sys.argv[2]); zpath=next(spool.glob("celikom-server-*.zip"))
with zipfile.ZipFile(zpath) as z:
 changed=[]
 for n in [x for x in z.namelist() if not x.endswith("/")]:
  target=stage/n
  a=hashlib.sha256(z.read(n)).hexdigest()
  b=hashlib.sha256(target.read_bytes()).hexdigest()
  if a!=b: changed.append((n,len(z.read(n)),a,b))
 print("CHANGED_FILE_COUNT",len(changed))
 for n,size,a,b in changed: print("DIFF",n,"zip_bytes",size,"zip_sha256",a,"stage_sha256",b)
PY
echo CELIKOM_SERVER_PACKAGE_DIFF_INVENTORY_OK
