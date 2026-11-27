#!/bin/bash
set -Eeuo pipefail
# Same-user cancellation of ONLY the previous 0.4.95 native test.
python3 <<'PY'
from pathlib import Path
import os,signal
st=Path("/srv/celikom/ci-runner/runner/celikom-build-spool").stat()
assert st.st_uid!=0
os.setgroups([]);os.setgid(st.st_gid);os.setuid(st.st_uid)
run=b"GITHUB_RUN_ID=46066362165";sha=b"GITHUB_SHA=6684c937e56b6a8dc6fb8dffcddab99f19c88a9a"
matched=0;target=0;denied=0
for p in Path("/proc").iterdir():
 if not p.name.isdigit():continue
 try:
  args=p.joinpath("cmdline").read_bytes().split(b"\0")
  if not any(a.endswith(b"scripts/test-audio-gain-browser.mjs") for a in args):continue
  target+=1
  env=p.joinpath("environ").read_bytes().split(b"\0")
  if run not in env or sha not in env:continue
  os.kill(int(p.name),signal.SIGTERM);matched+=1
  print("EXTENSION_095_OLD_NATIVE_TEST_TERMINATED",p.name)
 except PermissionError:denied+=1
 except OSError:continue
print("EXTENSION_095_OLD_NATIVE_SAFE_COUNTS",matched,target,denied)
PY
