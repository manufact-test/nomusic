#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/ci-runner/runner/celikom-build-spool/d7537830c054a7878b080e21b9ea91e21e29bc56-45433182374-1
python3 - "$S" /srv/celikom/app/staging-20261122 <<'PY'
import pathlib,zipfile,json,hashlib,sys
spool=pathlib.Path(sys.argv[1]); stage=pathlib.Path(sys.argv[2]); z=zipfile.ZipFile(next(spool.glob("celikom-server-*.zip")))
pack=set(n.rstrip("/") for n in z.namelist() if n and not n.endswith("/"))
staged=set()
for p in stage.rglob("*"):
 if p.is_file():
  rel=p.relative_to(stage).as_posix()
  if rel==".env" or rel.startswith(("storage/","vendor/")): continue
  staged.add(rel)
print("ZIP_FILES",len(pack),"STAGING_FILES_EXCLUDING_ENV_STORAGE_VENDOR",len(staged))
print("STAGING_ONLY_FILES")
for n in sorted(staged-pack): print("STAGE_ONLY",n)
print("ZIP_ONLY_FILES")
for n in sorted(pack-staged): print("ZIP_ONLY",n)
for p in [pathlib.Path("/srv/celikom/app/staging-20261122/package.json"),stage/"composer.json"]:
 if p.is_file():
  try:
   d=json.loads(p.read_text())
   print("VERSION_METADATA",p.name,{k:d.get(k) for k in ("name","version","description")})
  except Exception: pass
print("BUILD_PACKAGE_SHA256",hashlib.sha256(next(spool.glob("celikom-server-*.zip")).read_bytes()).hexdigest())
PY
echo CELIKOM_STAGE_FILESET_DIFF_OK
