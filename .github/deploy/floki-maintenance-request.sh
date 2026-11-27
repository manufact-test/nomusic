#!/bin/bash
set -Eeuo pipefail
# Restart only the idle CI01 listener; never signal any active job worker.
python3 <<'PY'
import subprocess
r=subprocess.run(["docker","top","celikom-floki-ci01","-eo","comm"],capture_output=True,text=True,timeout=15)
assert r.returncode==0
if "Runner.Worker" in r.stdout:
 print("EXTENSION_CI01_ACTIVE_WORKER_PRESERVED")
else:
 assert "Runner.Listener" in r.stdout
 r=subprocess.run(["docker","exec","--user","1000","celikom-floki-ci01","bash","-c","if pgrep -x Runner.Worker >/dev/null; then exit 42; fi; pkill -TERM -x Runner.Listener"],capture_output=True,text=True,timeout=15)
 if r.returncode==42:print("EXTENSION_CI01_LATE_WORKER_PRESERVED")
 else:
  assert r.returncode==0,"IDLE_LISTENER_SIGNAL_FAILED"
  print("EXTENSION_CI01_IDLE_LISTENER_SIGNALED_NO_WORKER_ACTIVE")
PY
