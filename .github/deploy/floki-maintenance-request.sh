#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PYREMOTE'
import subprocess,pathlib,time
unit='celikom-ci-runner2.service'
container='celikom-floki-ci02'
def run(args,timeout=20,check=True):
    p=subprocess.run(args,capture_output=True,text=True,errors='replace',timeout=timeout)
    if check and p.returncode:raise RuntimeError('COMMAND_FAILED '+args[0]+' '+str(p.returncode))
    return p
def out(*x):print(*x,flush=True)
def active():return run(['systemctl','is-active',unit],check=False).stdout.strip()
def processes():
    root=int(run(['docker','inspect','--format','{{.State.Pid}}',container]).stdout.strip())
    if root<=1:raise RuntimeError('INVALID_CONTAINER_PID')
    rows=run(['ps','-eo','pid=,ppid=,comm=']).stdout.splitlines()
    table={}
    for l in rows:
        a=l.strip().split(None,2)
        if len(a)==3 and a[0].isdigit() and a[1].isdigit():
            table[int(a[0])]=(int(a[1]),a[2])
    if root not in table:raise RuntimeError('CONTAINER_PID_NOT_FOUND')
    tree={root}
    while True:
        new={k for k,(p,n) in table.items() if p in tree}-tree
        if not new:break
        tree.update(new)
    return [table[k][1] for k in tree]
def workers(p):return sum('Runner.Worker' in x for x in p)
def listeners(p):return sum('Runner.Listener' in x for x in p)
p=processes()
out('CI02_BEFORE',active(),'listener='+str(listeners(p)),'worker='+str(workers(p)))
if active()!='active' or listeners(p)!=1 or workers(p):
    raise SystemExit('CI02_ACTIVE_OR_UNEXPECTED_NO_RESTART')
time.sleep(2)
p=processes()
if listeners(p)!=1 or workers(p):raise SystemExit('CI02_ACTIVE_WORKER_NO_RESTART')
out('CI02_RESTART_ONLY_EXISTING_SERVICE')
run(['systemctl','restart',unit],timeout=85)
for i in range(20):
    if active()=='active':
        try:
            p=processes()
            if listeners(p)==1:
                out('CI02_LISTENER_READY','worker='+str(workers(p)))
                break
        except Exception:pass
    time.sleep(2)
else:raise SystemExit('CI02_LISTENER_NOT_READY')
out('CI02_SERVICE_AFTER',run(['systemctl','show',unit,'--property=Id,ActiveState,SubState,MainPID,Result','--no-pager']).stdout.replace('\n',' ').strip())
out('A1_CI02_RESTART_DONE')
PYREMOTE
