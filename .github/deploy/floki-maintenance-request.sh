#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import json, pathlib, stat, subprocess
P=pathlib.Path
for unit in ['celikom-extension-owner.timer','celikom-extension-owner.service']:
 r=subprocess.run(['systemctl','is-active',unit],capture_output=True,text=True,timeout=15)
 print('OWNER_UNIT',unit,r.stdout.strip() or 'inactive')
 r=subprocess.run(['systemctl','is-enabled',unit],capture_output=True,text=True,timeout=15)
 print('OWNER_UNIT_ENABLED',unit,r.stdout.strip() or 'unknown')
p=P('/srv/celikom-releases/private/extension/current-owner.json')
if p.exists():
 assert stat.S_ISREG(p.lstat().st_mode) and not p.is_symlink() and p.stat().st_size<32768
 print('TRUSTED_CURRENT_OWNER',p.read_text())
else: print('TRUSTED_CURRENT_OWNER_MISSING')
root=P('/srv/celikom/ci-runner/runner/celikom-build-spool')
if root.exists():
 for d in root.iterdir():
  if not d.name.startswith('e52f819d6c69dc7e96734f60e14a17a92394b84c-'):continue
  p=d/'receipt.json'
  assert p.is_file() and not p.is_symlink() and p.stat().st_size<16384
  print('CANDIDATE_SPOOL',p.read_text())
print('EXTENSION_OWNER_READONLY_INSPECTION_DONE')
PY
