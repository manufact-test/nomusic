#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import subprocess,json,pathlib,re
for unit in ['celikom-mirror-sync.service','celikom-extension-owner.service']:
 r=subprocess.run(['systemctl','show',unit,'--property=Result,ExecMainStatus,ActiveState'],capture_output=True,text=True,timeout=10)
 print('DELIVERY_SERVICE_STATE',unit,r.stdout.strip().replace('\n',' '))
 r=subprocess.run(['journalctl','-u',unit,'-n','50','--no-pager','-o','cat'],capture_output=True,text=True,timeout=10)
 patterns=['Permission denied','Authentication failed','Could not resolve','Connection timed out','cannot lock ref','unable to access','not found','No space left','not a git repository','dubious ownership','unable to update local ref','Host key verification failed','timed out','EXTENSION_OWNER_']
 for p in patterns:
  n=r.stdout.lower().count(p.lower())
  if n:print('DELIVERY_LOG_CATEGORY',unit,p,n)
 for line in r.stdout.splitlines():
  if any(k in line.lower() for k in ['fatal:','error:','failed:']):
   line=re.sub(r'https?://[^\s]+','[URL]',line)
   line=re.sub(r'[A-Za-z0-9_=-]{45,}','[OPAQUE]',line)
   print('DELIVERY_SAFE_ERROR',line[:300])
git=['git','-c','safe.directory=/home/celikom-mirror/github-mirror.git','--git-dir=/home/celikom-mirror/github-mirror.git']
r=subprocess.run(git+['rev-parse','refs/heads/main'],capture_output=True,text=True,timeout=10)
if r.returncode==0:print('MIRROR_HEAD',r.stdout.strip())
r=subprocess.run(git+['show','refs/heads/main:.github/release/extension-owner-promotions.json'],capture_output=True,text=True,timeout=10)
if r.returncode==0:
 d=json.loads(r.stdout);print('MIRROR_APPROVED_VERSIONS',[a['version'] for a in d['approved']])
p=pathlib.Path('/srv/celikom-releases/private/extension/current-owner.json')
if p.exists():
 d=json.loads(p.read_text());print('OWNER_CURRENT_VERSION',d.get('version'));print('OWNER_CURRENT_DIGEST',d.get('sha256'))
print('DELIVERY_READONLY_STATE_DONE')
PY
