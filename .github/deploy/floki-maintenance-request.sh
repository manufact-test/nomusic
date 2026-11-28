#!/bin/bash
set -Eeuo pipefail
# Existing private spool producer, using the ACTUAL successful isolated build run.
python3 <<'PY'
from pathlib import Path
import subprocess,json,runpy,stat
a=json.loads("{\"version\":\"0.4.98\",\"source_commit\":\"4a10d2a70b3f97dc1ecc48624fa716b29200a7af\",\"run_id\":\"46133855457\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.98.zip\",\"size\":2507773,\"sha256\":\"76d190f9af494afb1634c873d1e734dd0a5944a64a326f32715d89e03daaa63d\"}")
location=json.loads("{\"directory\":\"/home/runner/celikom-build-spool/.work-extension98-owner.WvbFPx60\",\"node\":\"/home/runner/_work/_tool/node/24.22.3/x64/bin/node\",\"source\":\"4a10d2a70b3f97dc1ecc48624fa716b29200a7af\"}")
assert location["directory"].startswith("/home/runner/celikom-build-spool/.work-extension98-owner.")
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
print("EXTENSION_098_INDEPENDENT_PRIVATE_SPOOL_VERIFIED",json.dumps(a,sort_keys=True))
PY
