#!/bin/bash
set -Eeuo pipefail
# Publish only the exact approved owner candidate through the existing consumer.
python3 <<'PY'
import json,runpy,stat,subprocess,time
from pathlib import Path
a=json.loads("{\"version\":\"0.4.93\",\"source_commit\":\"eb70ee35d1be68b5dd5842d4fe6821c68ee487d0\",\"run_id\":\"45992977800\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.93.zip\",\"size\":2504603,\"sha256\":\"c97ec42c4317a33fc7cd390443a72feacf12c6f17efc6393db8d532e5bfb1de8\"}")
p=Path("/usr/local/lib/celikom-extension-release/consumer.py")
s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022
trusted=runpy.run_path(str(p))
sync=subprocess.run(["systemctl","start","celikom-mirror-sync.service"],capture_output=True,timeout=120)
print("EXTENSION_093_MIRROR_SYNC_EXIT",sync.returncode)
assert trusted["trusted_approvals"]().get(a["version"])==a
subprocess.run(["systemctl","start","celikom-extension-owner.service"],check=True,capture_output=True,timeout=180)
state=json.loads(trusted["read_file"](Path("/srv/celikom-releases/private/extension/current-owner.json"),4096,0))
expected={"version":a["version"],"sha256":a["sha256"],"size":a["size"],"filename":a["name"],"source_commit":a["source_commit"],"run_id":a["run_id"],"attempt":a["attempt"],"channel":"owner-only","https_verified":True}
assert state==expected
trusted["verify_https"](a)
print("EXTENSION_093_OWNER_RECEIPT_VERIFIED",json.dumps(state,sort_keys=True))
PY
