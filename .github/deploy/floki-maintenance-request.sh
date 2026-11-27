#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PYREMOTE'
import subprocess,re,collections,pathlib,os,shutil
def run(args,timeout=12):
    try:
        p=subprocess.run(args,capture_output=True,text=True,errors='replace',timeout=timeout)
        return p.returncode,p.stdout,p.stderr
    except Exception:
        return 99,'',''
def say(*x):print(*x,flush=True)
patterns={
    'JOB_RECEIVED':r'job request message received|job message received|running job:|received job request',
    'JOB_COMPLETED':r'job .* completed|job result|finish job',
    'LISTENING':r'listening for jobs|connected to github|session created',
    'JOB_ABORTED':r'job.*abandon|job.*cancel|job.*timeout|job.*not found',
    'SESSION_CONFLICT':r'sessionconflict|session conflict|already has an active session',
    'SESSION_LOST':r'session expired|session.*not found|session.*deleted|session.*lost',
    'AUTH_FAILURE':r'unauthorized|forbidden|authentication failed|access denied|status code.*40[13]',
    'DISK_FULL':r'no space left|disk full|enospc',
    'PERMISSION_FAILURE':r'permission denied|access to the path.*denied|unauthorizedaccessexception',
    'NETWORK_FAILURE':r'connection refused|connection reset|network is unreachable|name resolution|no such host|temporary failure in name resolution|timed out|timeout while connecting',
    'TLS_FAILURE':r'ssl connection|certificate verify|tls handshake|certificate.*invalid',
    'UPDATE_FAILURE':r'runner update.*fail|self.update.*fail|update.*required|runner version.*not supported',
    'WORKER_FAILURE':r'worker.*(?:crash|exit|failed|unable)|failed to start.*worker|worker process.*died',
    'RESOURCE_FAILURE':r'out of memory|oom.kill|cannot allocate memory|resource temporarily unavailable',
    'JOB_DISPATCH_FAILURE':r'failed to.*(?:job|dispatch)|job.*(?:lock|lease).*fail|job.*request.*not found',
    'ERROR_GENERIC':r'\[error\b|\berror:|\bexception:|\bfailed\b'
}
def summarize(label,data):
    lines=data.splitlines()[-1800:]
    counts={k:sum(bool(re.search(p,l,re.I)) for l in lines) for k,p in patterns.items()}
    say('RUNNER_LOG_SUMMARY',label,'lines='+str(len(lines)), ' '.join(k+'='+str(v) for k,v in counts.items() if v))
    for k,p in patterns.items():
        if k in ('ERROR_GENERIC','JOB_RECEIVED','JOB_COMPLETED','LISTENING'):continue
        matched=[l for l in lines if re.search(p,l,re.I)]
        if matched:
            stamp=re.search(r'20\d\d[-/]\d\d[-/]\d\d[T ]\d\d:\d\d:\d\d',matched[-1])
            say('RUNNER_LOG_LAST_EVENT',label,k,stamp.group(0) if stamp else 'timestamp-unavailable')
say('A1_RUNNER_HOST_READ_ONLY_BEGIN')
rc,out,err=run(['systemctl','list-units','--all','--type=service','--plain','--no-legend','--no-pager'])
units=[l.split()[0] for l in out.splitlines() if l.split() and re.search(r'actions\.runner|celikom.*(?:ci01|ci02|runner)|github.*runner',l,re.I)]
say('RUNNER_SYSTEMD_UNITS',len(units),'query_rc='+str(rc))
for u in units:
    rc2,o,e=run(['systemctl','show',u,'--no-pager','--property=ActiveState,SubState,Result,MainPID,NRestarts,ExecMainStatus,StateChangeTimestamp,WorkingDirectory'])
    props=dict(l.split('=',1) for l in o.splitlines() if '=' in l)
    say('RUNNER_UNIT',u,' '.join(k+'='+v for k,v in props.items() if k!='WorkingDirectory'))
    _,journal,_=run(['journalctl','-u',u,'--since','3 hours ago','-n','800','--no-pager','-o','short-iso'],20)
    summarize(u,journal)
    wd=props.get('WorkingDirectory','')
    if wd and wd.startswith('/') and wd!='/':
        diag=pathlib.Path(wd)/'_diag'
        try:
            files=sorted((f for f in diag.glob('Runner_*.log') if f.is_file()),key=lambda f:f.stat().st_mtime,reverse=True)[:2]
            for f in files:
                with f.open('rb') as h:
                    h.seek(max(0,f.stat().st_size-384000)); data=h.read().decode('utf-8','replace')
                summarize(u+'/diag',data)
        except Exception as e:say('RUNNER_DIAG_UNAVAILABLE',u,type(e).__name__)
rc,ps,_=run(['ps','-eo','comm='])
counts=collections.Counter(x.strip() for x in ps.splitlines())
say('RUNNER_PROCESS_COUNTS',' '.join(k+'='+str(v) for k,v in counts.items() if re.search(r'Runner\.(Listener|Worker)|runsvc|RunnerService',k,re.I)) or 'none')
if shutil.which('docker'):
    rc,containers,_=run(['docker','ps','-a','--format','{{.Names}}\t{{.Status}}'])
    matches=[l for l in containers.splitlines() if re.search(r'ci01|ci02|runner|github.actions',l,re.I)]
    say('RUNNER_CONTAINERS',len(matches),'query_rc='+str(rc))
    for l in matches:
        name,status=l.split('\t',1)
        if re.fullmatch(r'[A-Za-z0-9_.-]+',name):
            say('RUNNER_CONTAINER',name,status)
            _,o,e=run(['docker','logs','--since','3h','--tail','1000',name],20)
            summarize(name,o+'\n'+e)
for path in ('/','/home/runner','/tmp'):
    if os.path.isdir(path):
        d=shutil.disk_usage(path)
        v=os.statvfs(path)
        say('HOST_STORAGE',path,'free_MiB='+str(d.free//1048576),'inode_free_pct='+str(round(v.f_favail/max(1,v.f_files)*100,1)))
try:
    mem=dict((l.split(':',1)[0],l.split(':',1)[1].strip()) for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if ':' in l)
    say('HOST_MEMORY_AVAILABLE',mem.get('MemAvailable','unknown'))
except Exception:pass
for host in ('github.com','api.github.com','pipelines.actions.githubusercontent.com'):
    rc,_,_=run(['getent','ahostsv4',host],8)
    say('HOST_DNS',host,'OK' if rc==0 else 'FAIL')
say('A1_RUNNER_HOST_READ_ONLY_DONE')
PYREMOTE
