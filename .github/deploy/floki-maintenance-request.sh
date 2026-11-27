#!/bin/bash
set -Eeuo pipefail
# Read-only CI01 availability check; no service/process/config changes.
python3 <<'PY'
import subprocess,json
r=subprocess.run(["docker","inspect","celikom-floki-ci01","--format","{{json .State}}"],capture_output=True,text=True,timeout=15)
if r.returncode==0:
 d=json.loads(r.stdout);print("EXTENSION_CI01_STATE",json.dumps({k:d.get(k) for k in ["Running","Paused","Restarting","OOMKilled","Status","StartedAt"]}))
r=subprocess.run(["docker","top","celikom-floki-ci01","-eo","pid,comm"],capture_output=True,text=True,timeout=15)
if r.returncode==0:print("EXTENSION_CI01_PROCESS_NAMES",r.stdout[:4000])
r=subprocess.run(["docker","exec","--user","1000","celikom-floki-ci01","bash","-c","command -v node || true; find /opt/hostedtoolcache/node /home/runner/_work/_tool/node -maxdepth 4 -type f -path '*/bin/node' 2>/dev/null | head -4"],capture_output=True,text=True,timeout=15)
print("EXTENSION_CI01_NODE_PATHS",r.returncode,r.stdout[:1000])
PY
