#!/bin/bash
set -Eeuo pipefail
# Recover ONLY the idle CI01 listener. Never restart any active worker or CI02.
python3 <<'PY'
from pathlib import Path
import subprocess,stat
p=Path("/etc/systemd/system/celikom-ci-runner.service")
assert p.is_file() and not p.is_symlink() and p.stat().st_uid==0
unit=p.read_text()
assert "celikom-floki-ci01" in unit and "docker" in unit
r=subprocess.run(["docker","top","celikom-floki-ci01","-eo","comm"],capture_output=True,text=True,timeout=15)
assert r.returncode==0
if "Runner.Worker" in r.stdout:
 print("EXTENSION_CI01_ACTIVE_WORKER_PRESERVED")
else:
 assert "Runner.Listener" in r.stdout
 subprocess.run(["systemctl","restart","celikom-ci-runner.service"],check=True,capture_output=True,timeout=45)
 subprocess.run(["systemctl","is-active","celikom-ci-runner.service"],check=True,capture_output=True,timeout=10)
 print("EXTENSION_CI01_IDLE_LISTENER_RESTARTED_NO_WORKER_WAS_ACTIVE")
PY
