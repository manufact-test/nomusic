#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/ci-runner/runner/celikom-build-spool/d7537830c054a7878b080e21b9ea91e21e29bc56-45433182374-1
python3 - "$S" /srv/celikom/app/staging-20261122 <<'PY'
import pathlib,zipfile,difflib,sys,re
spool=pathlib.Path(sys.argv[1]); stage=pathlib.Path(sys.argv[2]); zpath=next(spool.glob("celikom-server-*.zip"))
with zipfile.ZipFile(zpath) as z:
 for name in ["config/app.php","src/Admin/AdminPanel.php","src/Admin/ModerationService.php","src/Application/UploadService.php"]:
  a=z.read(name).decode("utf-8",errors="replace").splitlines()
  b=(stage/name).read_text(errors="replace").splitlines()
  diff=list(difflib.unified_diff(b,a,fromfile="Hostinger-import/"+name,tofile="Floki-build/"+name,n=2))
  print("=== DIFF",name,"changed_lines",sum(1 for x in diff if x.startswith(("+","-")) and not x.startswith(("+++","---"))),"===")
  if name=="config/app.php":
   chosen=[x for x in diff if x.startswith(("@@","+++","---")) or ("CELIKOM_" in x or "mail_" in x or "upload_" in x or "storage_" in x)]
  else:
   chosen=[x for x in diff if x.startswith(("@@","+++","---")) or x.startswith(("+","-"))]
  print("\n".join(chosen[:90]))
PY
echo CELIKOM_BACKEND_CODE_DIFF_REVIEW_READY
