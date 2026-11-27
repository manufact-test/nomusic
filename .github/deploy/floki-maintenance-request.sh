#!/bin/bash
set -Eeuo pipefail
# Existing private spool producer, using the ACTUAL successful isolated build run.
python3 <<'PY'
from pathlib import Path
import subprocess,json,runpy,stat
a=json.loads("{\"version\":\"0.4.96\",\"source_commit\":\"0e28cba5221c0f345bb1e3502d186016a614f54b\",\"run_id\":\"46070419007\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.96.zip\",\"size\":2506160,\"sha256\":\"2503ea6f3a2326394dbd3e67859064a051db30125a035f44cff22c35aefc1379\"}")
location=json.loads("{\"directory\":\"/home/runner/celikom-build-spool/.work-extension96-owner.N2PzTsPO\",\"node\":\"/home/runner/_work/_tool/node/24.22.3/x64/bin/node\",\"source\":\"0e28cba5221c0f345bb1e3502d186016a614f54b\"}")
assert location["directory"].startswith("/home/runner/celikom-build-spool/.work-extension96-owner.")
assert location["source"]==a["source_commit"]
uid=str(Path("/srv/celikom/ci-runner/runner/celikom-build-spool").stat().st_uid)
assert uid!="0"
args=["docker","exec","--user",uid,"--workdir",location["directory"],"celikom-floki-ci01",location["node"],".github/scripts/floki-private-build-spool.mjs",location["directory"],"/home/runner/celikom-build-spool",a["source_commit"],a["run_id"],a["attempt"],"--extension-only"]
r=subprocess.run(args,capture_output=True,text=True,timeout=60)
print(r.stdout[-2000:],end="")
assert r.returncode==0,"EXISTING_PRIVATE_PRODUCER_FAILED"
p=Path("/usr/local/lib/celikom-extension-release/consumer.py")
st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not st.st_mode & 0o022
trusted=runpy.run_path(str(p));data=trusted["verify_spool"](a)
assert len(data)==a["size"]
print("EXTENSION_096_INDEPENDENT_PRIVATE_SPOOL_VERIFIED",json.dumps(a,sort_keys=True))
PY
