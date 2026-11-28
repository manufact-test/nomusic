#!/bin/bash
set -Eeuo pipefail
# Existing trusted consumer: exact owner package, full HTTPS hashes, own temp cleanup.
python3 <<'PY'
from pathlib import Path
import subprocess,json,runpy,stat,hashlib
a=json.loads("{\"version\":\"0.4.98\",\"source_commit\":\"4a10d2a70b3f97dc1ecc48624fa716b29200a7af\",\"run_id\":\"46133855457\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.98.zip\",\"size\":2507773,\"sha256\":\"76d190f9af494afb1634c873d1e734dd0a5944a64a326f32715d89e03daaa63d\"}")
p=Path("/usr/local/lib/celikom-extension-release/consumer.py");s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022
trusted=runpy.run_path(str(p))
backend=Path("/srv/celikom/app/staging-20261122")
for name,digest in {"tools/m4a-normalizer":"c0f2d9b74c0f1f4e19605d45dbaf3e31e75411a53da4f1ceb172c1e2e0b86d63","src/Application/M4aNormalizer.php":"6e183fa340db660f4c5fd9137eb850549a2490872a3f34bbbf44fcf995a4e623","src/Application/UploadService.php":"27ff9aa9614bc7ee7815779dcc4851ed1aa1c736fe6084ccc9e46bf60d85e5b6"}.items():
 assert hashlib.sha256((backend/name).read_bytes()).hexdigest()==digest
print("EXTENSION_098_LIVE_M4A_BACKEND_HASHES_VERIFIED")
r=subprocess.run(["systemctl","start","celikom-mirror-sync.service"],capture_output=True,timeout=120)
print("EXTENSION_098_MIRROR_SYNC_EXIT",r.returncode)
assert trusted["trusted_approvals"]().get(a["version"])==a
subprocess.run(["systemctl","start","celikom-extension-owner.service"],check=True,capture_output=True,timeout=180)
state=json.loads(trusted["read_file"](Path("/srv/celikom-releases/private/extension/current-owner.json"),4096,0))
expected={"version":a["version"],"sha256":a["sha256"],"size":a["size"],"filename":a["name"],"source_commit":a["source_commit"],"run_id":a["run_id"],"attempt":a["attempt"],"channel":"owner-only","https_verified":True}
assert state==expected
trusted["verify_https"](a)
print("EXTENSION_098_OWNER_RECEIPT_VERIFIED",json.dumps(state,sort_keys=True))
location=json.loads("{\"directory\":\"/home/runner/celikom-build-spool/.work-extension98-owner.WvbFPx60\",\"node\":\"/home/runner/_work/_tool/node/24.22.3/x64/bin/node\",\"source\":\"4a10d2a70b3f97dc1ecc48624fa716b29200a7af\"}")
assert location["directory"].startswith("/home/runner/celikom-build-spool/.work-extension98-owner.") and location["directory"].count("/")==4
uid=str(Path("/srv/celikom/ci-runner/runner/celikom-build-spool").stat().st_uid);assert uid!="0"
subprocess.run(["docker","exec","--user",uid,"celikom-floki-ci01","rm","-rf","--",location["directory"]],check=True,capture_output=True,timeout=30)
print("EXTENSION_098_OWN_ISOLATED_BUILD_DIRECTORY_CLEANED")
PY
