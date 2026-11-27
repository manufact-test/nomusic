#!/bin/bash
set -Eeuo pipefail
# Existing trusted owner consumer only; verify exact package and HTTPS bytes.
python3 <<'PY'
import json,runpy,stat,subprocess
from pathlib import Path
a=json.loads("{\"version\":\"0.4.94\",\"source_commit\":\"81447bfef49a2492675ff0574a0eaa986ed79282\",\"run_id\":\"46059173025\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.94.zip\",\"size\":2505077,\"sha256\":\"e381d4c4274c768b888ab279d6523c666944f6d34aba581e70cdc92e22d09e09\"}")
p=Path("/usr/local/lib/celikom-extension-release/consumer.py")
s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022
trusted=runpy.run_path(str(p))
sync=subprocess.run(["systemctl","start","celikom-mirror-sync.service"],capture_output=True,timeout=120)
print("EXTENSION_094_MIRROR_SYNC_EXIT",sync.returncode)
assert trusted["trusted_approvals"]().get(a["version"])==a
subprocess.run(["systemctl","start","celikom-extension-owner.service"],check=True,capture_output=True,timeout=180)
state=json.loads(trusted["read_file"](Path("/srv/celikom-releases/private/extension/current-owner.json"),4096,0))
expected={"version":a["version"],"sha256":a["sha256"],"size":a["size"],"filename":a["name"],"source_commit":a["source_commit"],"run_id":a["run_id"],"attempt":a["attempt"],"channel":"owner-only","https_verified":True}
assert state==expected
trusted["verify_https"](a)
print("EXTENSION_094_OWNER_RECEIPT_VERIFIED",json.dumps(state,sort_keys=True))
PY
