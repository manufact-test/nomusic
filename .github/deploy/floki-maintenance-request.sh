#!/bin/bash
set -Eeuo pipefail
# Existing trusted consumer: exact owner package, full HTTPS hashes, own temp cleanup.
python3 <<'PY'
from pathlib import Path
import subprocess,json,runpy,stat
a=json.loads("{\"version\":\"0.4.96\",\"source_commit\":\"0e28cba5221c0f345bb1e3502d186016a614f54b\",\"run_id\":\"46070419007\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.96.zip\",\"size\":2506160,\"sha256\":\"2503ea6f3a2326394dbd3e67859064a051db30125a035f44cff22c35aefc1379\"}")
p=Path("/usr/local/lib/celikom-extension-release/consumer.py");s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022
trusted=runpy.run_path(str(p))
r=subprocess.run(["systemctl","start","celikom-mirror-sync.service"],capture_output=True,timeout=120)
print("EXTENSION_096_MIRROR_SYNC_EXIT",r.returncode)
assert trusted["trusted_approvals"]().get(a["version"])==a
subprocess.run(["systemctl","start","celikom-extension-owner.service"],check=True,capture_output=True,timeout=180)
state=json.loads(trusted["read_file"](Path("/srv/celikom-releases/private/extension/current-owner.json"),4096,0))
expected={"version":a["version"],"sha256":a["sha256"],"size":a["size"],"filename":a["name"],"source_commit":a["source_commit"],"run_id":a["run_id"],"attempt":a["attempt"],"channel":"owner-only","https_verified":True}
assert state==expected
trusted["verify_https"](a)
print("EXTENSION_096_OWNER_RECEIPT_VERIFIED",json.dumps(state,sort_keys=True))
location=json.loads("{\"directory\":\"/home/runner/celikom-build-spool/.work-extension96-owner.N2PzTsPO\",\"node\":\"/home/runner/_work/_tool/node/24.22.3/x64/bin/node\",\"source\":\"0e28cba5221c0f345bb1e3502d186016a614f54b\"}")
assert location["directory"].startswith("/home/runner/celikom-build-spool/.work-extension96-owner.") and location["directory"].count("/")==4
uid=str(Path("/srv/celikom/ci-runner/runner/celikom-build-spool").stat().st_uid);assert uid!="0"
subprocess.run(["docker","exec","--user",uid,"celikom-floki-ci01","rm","-rf","--",location["directory"]],check=True,capture_output=True,timeout=30)
print("EXTENSION_096_OWN_ISOLATED_BUILD_DIRECTORY_CLEANED")
PY
