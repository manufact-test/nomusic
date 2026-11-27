#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PYREMOTE'
import subprocess,re,time
unit='celikom-ci-runner2.service'
container='celikom-floki-ci02'
def run(args,timeout=20,check=True):
    p=subprocess.run(args,capture_output=True,text=True,errors='replace',timeout=timeout)
    if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+args[0]+' '+str(p.returncode))
    return p
def out(*x):print(*x,flush=True)
def active():
    return run(['systemctl','is-active',unit],check=False).stdout.strip()
def processes():
    return run(['docker','top',container,'-eo','comm']).stdout.splitlines()[1:]
logs=run(['docker','logs','--since','80m','--tail','140',container],check=False)
for line in (logs.stdout+'\n'+logs.stderr).splitlines():
    if not re.search(r'job|worker|session|error|exception|listen|update',line,re.I):continue
    if re.search(r'(?i)token|authorization|password|secret|credential|cookie|https?://',line):continue
    line=re.sub(r'\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b','[id]',line,flags=re.I)
    line=re.sub(r'\b[A-Za-z0-9_+/=-]{24,}\b','[redacted]',line)
    out('CI02_RECENT',line[:250])
p=processes()
out('CI02_BEFORE',active(),'listener='+str(sum('Runner.Listener' in x for x in p)),'worker='+str(sum('Runner.Worker' in x for x in p)))
if active()!='active' or not any('Runner.Listener' in x for x in p):
    raise SystemExit('CI02_UNEXPECTED_SERVICE_STATE_NO_RESTART')
if any('Runner.Worker' in x for x in p):
    raise SystemExit('CI02_WORKER_ACTIVE_NO_RESTART')
out('CI02_RESTART_ONLY_EXISTING_SERVICE')
run(['systemctl','restart',unit],timeout=85)
for i in range(12):
    if active()=='active':
        try:
            p=processes()
            if any('Runner.Listener' in x for x in p):
                out('CI02_LISTENER_READY','worker='+str(sum('Runner.Worker' in x for x in p)))
                break
        except Exception:pass
    time.sleep(2)
else:raise SystemExit('CI02_LISTENER_NOT_READY')
out('CI02_SERVICE_AFTER',run(['systemctl','show',unit,'--property=Id,ActiveState,SubState,MainPID,Result','--no-pager']).stdout.replace('\n',' ').strip())
out('A1_CI02_RESTART_DONE')
PYREMOTE
