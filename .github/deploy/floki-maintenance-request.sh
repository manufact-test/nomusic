#!/bin/bash
set -Eeuo pipefail
# Independent read-only verification of the exact private owner candidate.
python3 <<'PY'
import json,runpy,stat,time
from pathlib import Path
a=json.loads("{\"version\":\"0.4.95\",\"source_commit\":\"6684c937e56b6a8dc6fb8dffcddab99f19c88a9a\",\"run_id\":\"46066362165\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.95.zip\",\"size\":2505631,\"sha256\":\"ef0ddd9f1e0cfc5e2649ad360c2ae82b8ec8af815249e28150e68f412be05a40\"}")
p=Path("/usr/local/lib/celikom-extension-release/consumer.py")
s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022
trusted=runpy.run_path(str(p))
receipt=Path("/srv/celikom/ci-runner/runner/celikom-build-spool")/(a["source_commit"]+"-"+a["run_id"]+"-"+a["attempt"])/"receipt.json"
for _ in range(15):
 if receipt.exists():break
 time.sleep(3)
data=trusted["verify_spool"](a)
assert len(data)==a["size"]
print("EXTENSION_095_PRIVATE_SPOOL_VERIFIED",json.dumps(a,sort_keys=True))
PY
