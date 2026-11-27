#!/bin/bash
set -Eeuo pipefail
# Exact approved private owner candidate through the existing trusted consumer.
python3 <<'PY'
import json,runpy,stat,subprocess
from pathlib import Path
a=json.loads("{\"version\":\"0.4.95\",\"source_commit\":\"6684c937e56b6a8dc6fb8dffcddab99f19c88a9a\",\"run_id\":\"46066362165\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.95.zip\",\"size\":2505631,\"sha256\":\"ef0ddd9f1e0cfc5e2649ad360c2ae82b8ec8af815249e28150e68f412be05a40\"}")
p=Path("/usr/local/lib/celikom-extension-release/consumer.py")
s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022
trusted=runpy.run_path(str(p))
sync=subprocess.run(["systemctl","start","celikom-mirror-sync.service"],capture_output=True,timeout=120)
print("EXTENSION_095_MIRROR_SYNC_EXIT",sync.returncode)
assert trusted["trusted_approvals"]().get(a["version"])==a
subprocess.run(["systemctl","start","celikom-extension-owner.service"],check=True,capture_output=True,timeout=180)
state=json.loads(trusted["read_file"](Path("/srv/celikom-releases/private/extension/current-owner.json"),4096,0))
expected={"version":a["version"],"sha256":a["sha256"],"size":a["size"],"filename":a["name"],"source_commit":a["source_commit"],"run_id":a["run_id"],"attempt":a["attempt"],"channel":"owner-only","https_verified":True}
assert state==expected
trusted["verify_https"](a)
print("EXTENSION_095_OWNER_RECEIPT_VERIFIED",json.dumps(state,sort_keys=True))
PY
