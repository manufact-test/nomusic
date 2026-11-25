#!/bin/bash
set -Eeuo pipefail
umask 077
# Read-only runner inventory. Never read or emit credentials.
python3 - <<'PY'
import json,subprocess,pathlib,os
def out(*cmd): return subprocess.check_output(cmd,text=True).strip()
print('MEMORY_SUMMARY',out('free','-m'))
print('CPU_COUNT',out('nproc'))
print('CPU_LOAD',pathlib.Path('/proc/loadavg').read_text().strip())
print('DISK',out('df','-h','/srv/celikom/ci-runner'))
print('UNIT_LIMITS',out('systemctl','show','celikom-ci.slice','-p','CPUQuotaPerSecUSec','-p','MemoryMax','-p','MemoryHigh','-p','MemorySwapMax','-p','TasksMax'))
print('RUNNER_SERVICE',out('systemctl','show','celikom-ci-runner.service','-p','ActiveState','-p','SubState','-p','Slice','-p','FragmentPath'))
for cid in out('docker','ps','-q').splitlines():
 d=json.loads(out('docker','inspect',cid))[0]
 if not ('runner' in d['Name'].lower() or 'actions-runner' in d['Config']['Image']):continue
 h=d['HostConfig']
 print('RUNNER',json.dumps({'name':d['Name'],'image':d['Config']['Image'],'user':d['Config']['User'],'mounts':[{'source':m['Source'],'destination':m['Destination'],'rw':m['RW']} for m in d['Mounts']],'network':h['NetworkMode'],'memory':h['Memory'],'memory_swap':h['MemorySwap'],'nano_cpus':h['NanoCpus'],'pids_limit':h['PidsLimit'],'cgroup_parent':h['CgroupParent'],'cap_drop':h['CapDrop'],'security_opt':h['SecurityOpt'],'readonly_rootfs':h['ReadonlyRootfs'],'privileged':h['Privileged'],'tmpfs':h.get('Tmpfs'),'entrypoint':d['Config']['Entrypoint']},sort_keys=True))
print('RUNNER_LIVE_STATS',out('docker','stats','--no-stream','--format','{{.Name}} {{.CPUPerc}} {{.MemUsage}}'))
for p in ['/srv/celikom/ci-runner/runner','/srv/celikom/ci-runner/runner/celikom-build-spool','/srv/celikom/ci-runner/runner2']:
 q=pathlib.Path(p)
 if q.exists():
  s=q.stat();print('DIRECTORY',p,s.st_uid,s.st_gid,oct(s.st_mode&0o777))
PY
echo CELIKOM_RUNNER_CAPACITY_READONLY_OK

# Execute read-only capacity check.
