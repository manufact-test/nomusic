#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo A1_ROOT_RECEIPT_AUDIT_BEGIN
for unit in celikom-a1-signed-owner.timer celikom-a1-signed-owner.service; do
  echo "A1_UNIT $unit"
  if systemctl cat "$unit" >/dev/null 2>&1; then
    systemctl show "$unit" --property ActiveState,SubState,Result,ExecMainStatus,NRestarts,MainPID,LastTriggerUSec,NextElapseUSecRealtime,StateChangeTimestamp --no-pager
  else
    echo A1_UNIT_MISSING
  fi
done
receipt=/srv/celikom/ci-runner/runner/celikom-a1-signed-spool/receipts/a1-46121780348-1.json
if [[ -f "$receipt" && ! -L "$receipt" ]]; then
  python3 - "$receipt" <<'PY'
import json,os,stat,sys,re
p=sys.argv[1];s=os.stat(p,follow_symlinks=False);r=json.load(open(p))
u=r.get("url","")
ok=bool(re.fullmatch(r"https://celikom\.com/downloads/a1/[0-9a-f]{48}/CELIKOM-A1-RAMIL-AU-BETA31-HONOR50-20261128\.apk",u))
print("A1_RECEIPT_PRESENT", "owner",s.st_uid,"mode",oct(stat.S_IMODE(s.st_mode)),
      "run",r.get("run"),"attempt",r.get("attempt"),"name",r.get("name"),
      "size",r.get("size"),"sha256_match",r.get("sha256")=="fed4b9c150e45eadc6cc424b2a904f5ac5951160ef1e1e8c9227c039f37562fe",
      "https_verified",r.get("https_verified") is True,"url_shape_valid",ok)
PY
else
  echo A1_RECEIPT_NOT_PRESENT
fi
echo A1_ROOT_RECENT_EVENT_COUNTS
journalctl -u celikom-a1-signed-owner.service --since '-30 minutes' --no-pager -o cat 2>/dev/null | grep -Eo 'A1_ROOT_[A-Z0-9_]+' | sort | uniq -c || true
echo A1_ROOT_RECEIPT_AUDIT_DONE
