#!/bin/bash
set -Eeuo pipefail
# Stop only the previous private 0.4.95 run's already waived, hung native test.
python3 <<'PY'
from pathlib import Path
import os,signal
run=b"GITHUB_RUN_ID=46066362165"
sha=b"GITHUB_SHA=6684c937e56b6a8dc6fb8dffcddab99f19c88a9a"
matched=0
for p in Path("/proc").iterdir():
 if not p.name.isdigit():continue
 try:
  args=p.joinpath("cmdline").read_bytes().split(b"\0")
  if not any(a.endswith(b"scripts/test-audio-gain-browser.mjs") for a in args):continue
  if p.joinpath("comm").read_text().strip()!="node":continue
  env=p.joinpath("environ").read_bytes().split(b"\0")
  if run not in env or sha not in env:continue
  if p.stat().st_uid==0:continue
  os.kill(int(p.name),signal.SIGTERM)
  print("EXTENSION_095_OLD_NATIVE_TEST_TERMINATED",p.name)
  matched+=1
 except (OSError,ProcessLookupError):continue
print("EXTENSION_095_OLD_NATIVE_MATCH_COUNT",matched)
PY
