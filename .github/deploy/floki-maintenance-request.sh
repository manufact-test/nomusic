#!/bin/bash
set -Eeuo pipefail
# Read-only, independent verification of the exact private extension candidate.
python3 <<'PY'
import json,runpy,stat
from pathlib import Path
a=json.loads("{\"version\":\"0.4.93\",\"source_commit\":\"eb70ee35d1be68b5dd5842d4fe6821c68ee487d0\",\"run_id\":\"45992977800\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.93.zip\",\"size\":2504603,\"sha256\":\"c97ec42c4317a33fc7cd390443a72feacf12c6f17efc6393db8d532e5bfb1de8\"}")
p=Path("/usr/local/lib/celikom-extension-release/consumer.py")
s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022
trusted=runpy.run_path(str(p))
data=trusted["verify_spool"](a)
assert len(data)==a["size"]
print("EXTENSION_093_PRIVATE_SPOOL_VERIFIED",json.dumps(a,sort_keys=True))
PY
