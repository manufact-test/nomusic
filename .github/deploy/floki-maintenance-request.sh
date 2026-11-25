#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Install dedicated unprivileged APK-only transport and narrowly scoped HTTPS route.
python3 - <<'PY'
import pathlib as pl, os, stat, pwd, grp, subprocess, tempfile, re
P=pl.Path
gate=P('/usr/local/sbin/celikom-deploy-gateway')
conf=P('/etc/nginx/sites-available/celikom-site-https')
receiver=P('/usr/local/sbin/celikom-a1-apk-receive')
base=P('/srv/celikom-a1-downloads')
state=P('/root/celikom-a1-delivery-bootstrap-v2')
for p in [gate,conf]:
 st=p.lstat(); assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not(st.st_mode&0o022)
assert not state.exists() and not receiver.exists() and not base.exists()
old_gate=gate.read_text(); old_conf=conf.read_text()
assert 'auth_basic "CELIKOM private review";' in old_conf
anchor='  *) echo FLOKI_DEPLOY_COMMAND_REFUSED >&2; exit 64 ;;'
assert old_gate.count(anchor)==1 and 'receive-a1-apk' not in old_gate
assert '/downloads/a1/' not in old_conf
assert not re.search(r'location\s+\^~\s+/downloads(?:/|\s)',old_conf)
entry='    location = /downloads/extension/celikom-extension-0.4.73.zip {'
assert old_conf.count(entry)==1
route=r'''    # A1 owner capability links; APK-only, no GitHub login, no listing.
    location ~ "^/downloads/a1/(?<a1token>[0-9a-f]{48})/(?<a1file>CELIKOM-A1-[A-Za-z0-9_-]{1,100}\.apk)$" {
        auth_basic off;
        alias /srv/celikom-a1-downloads/files/$a1token/$a1file;
        disable_symlinks on from=/srv/celikom-a1-downloads;
        autoindex off;
        access_log off;
        error_log /dev/null crit;
        limit_except GET { deny all; }
        types { application/vnd.android.package-archive apk; }
        default_type application/vnd.android.package-archive;
        add_header Content-Disposition "attachment" always;
        add_header Cache-Control "private, no-store" always;
        add_header Referrer-Policy "no-referrer" always;
        add_header X-Robots-Tag "noindex, nofollow, noarchive" always;
        add_header X-Content-Type-Options nosniff always;
    }
    location /downloads/a1/ { auth_basic off; return 404; }
'''
handler=r'''#!/usr/bin/python3
import sys, os, stat, re, json, hashlib, secrets, pathlib, tempfile, fcntl, time
from contextlib import suppress
P=pathlib.Path
base=P('/srv/celikom-a1-downloads')
files=base/'files'
private=base/'receipts'
# Existing deploy identity only; no sudo, no commands or arbitrary paths from input.
assert os.geteuid()!=0
assert len(sys.argv)==1
def fail(): raise SystemExit('A1_INTAKE_REJECTED')
def reg(p):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.geteuid(): fail()
 return s
os.umask(0o077)
header=sys.stdin.buffer.readline(4097)
if len(header)>4096 or not header.endswith(b'\n'): fail()
try: m=json.loads(header)
except Exception: fail()
if set(m)!={'run','attempt','name','size','sha256'}: fail()
run,attempt,name,size,digest=[m[k] for k in ('run','attempt','name','size','sha256')]
if type(run)!=int or not 1<=run<=10**14 or type(attempt)!=int or not 1<=attempt<=100: fail()
if not isinstance(name,str) or not re.fullmatch(r'CELIKOM-A1-[A-Za-z0-9_-]{1,100}\.apk',name): fail()
if type(size)!=int or not 1024*1024<=size<=160*1024*1024: fail()
if not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}',digest): fail()
for p in (files,private):
 s=p.lstat()
 if not stat.S_ISDIR(s.st_mode) or s.st_uid!=os.geteuid(): fail()
with (private/'lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 # No overwrite; exact repeated run returns same private capability.
 receipt=private/(str(run)+'-'+str(attempt)+'.json')
 old=None
 if receipt.exists():
  reg(receipt)
  old=json.loads(receipt.read_text())
  if old.get('metadata')!=m: fail()
  token=old.get('token')
  if not isinstance(token,str) or not re.fullmatch('[0-9a-f]{48}',token): fail()
  dest=files/token/name
  reg(dest)
  if dest.stat().st_size!=size: fail()
  with dest.open('rb') as f:
   if hashlib.file_digest(f,'sha256').hexdigest()!=digest: fail()
 else:
  token=secrets.token_hex(24)
 # Cap all retained payloads; never delete prior owner builds silently.
 used=sum(p.stat().st_size for p in files.glob('*/*.apk') if p.is_file() and not p.is_symlink())
 if old is None and used+size>2*1024**3: fail()
 temp=None
 try:
  # Temporary payload outside HTTP-visible path. Hash streaming, exact EOF.
  with tempfile.NamedTemporaryFile(dir=private,delete=False) as f:
   temp=P(f.name); h=hashlib.sha256(); n=0
   while n<size:
    b=sys.stdin.buffer.read(min(size-n,1024*1024))
    if not b: fail()
    if n==0 and b[:4]!=b'PK\x03\x04': fail()
    n+=len(b); h.update(b); f.write(b)
   if sys.stdin.buffer.read(1) or h.hexdigest()!=digest: fail()
   f.flush();os.fsync(f.fileno())
  if old is None:
   d=files/token
   d.mkdir(mode=0o700)
   try:
    os.chmod(temp,0o644)
    os.replace(temp,d/name)
    os.chmod(d,0o755)
    with receipt.open('x') as f:
     json.dump({'metadata':m,'token':token,'created':int(time.time())},f)
   except BaseException:
    with suppress(FileNotFoundError): (d/name).unlink()
    with suppress(OSError): d.rmdir()
    raise
  print('A1_DOWNLOAD_URL=https://celikom.com/downloads/a1/'+token+'/'+name)
  print('A1_RECEIVED_SHA256='+digest)
 finally:
  if temp is not None:
   with suppress(FileNotFoundError): temp.unlink()
'''
state.mkdir(mode=0o700)
(state/'gateway.original').write_text(old_gate);(state/'nginx.original').write_text(old_conf)
new_gate=old_gate.replace(anchor,'  receive-a1-apk) exec timeout 300 /usr/local/sbin/celikom-a1-apk-receive ;;\n'+anchor)
new_conf=old_conf.replace(entry,route+'\n'+entry)
uid=pwd.getpwnam('celikom-deploy').pw_uid; gid=pwd.getpwnam('celikom-deploy').pw_gid
def atomic(path,body,mode):
 with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:
  tmp=P(f.name);f.write(body.encode());f.flush();os.fsync(f.fileno())
 try:
  os.chmod(tmp,mode);os.replace(tmp,path)
 finally:
  if tmp.exists():tmp.unlink()
try:
 base.mkdir(mode=0o711);os.chmod(base,0o711)
 for name,mode in [('files',0o711),('receipts',0o700)]:
  d=base/name;d.mkdir(mode=mode);os.chown(d,uid,gid);os.chmod(d,mode)
 atomic(receiver,handler,0o755)
 compile(handler,str(receiver),'exec')
 atomic(gate,new_gate,0o755);subprocess.run(['bash','-n',str(gate)],check=True)
 atomic(conf,new_conf,stat.S_IMODE(conf.stat().st_mode))
 subprocess.run(['nginx','-t'],check=True)
 subprocess.run(['systemctl','reload','nginx'],check=True)
 # No authentication change outside the dedicated regex.
 import urllib.request, urllib.error
 def status(url):
  try:
   with urllib.request.urlopen(url,timeout=15) as r: return r.status
  except urllib.error.HTTPError as e:return e.code
 assert status('https://celikom.com/')==401
 assert status('https://celikom.com/downloads/extension/celikom-extension-0.4.73.zip')==401
 assert status('https://celikom.com/updates/android/stable.json')==401
 assert status('https://celikom.com/downloads/a1/')==404
 assert status('https://celikom.com/downloads/a1/'+'0'*48+'/CELIKOM-A1-TEST.apk')==404
 assert status('https://api.celikom.com/api/v1/health')==200
 print('CELIKOM_A1_APK_ONLY_UNPRIVILEGED_INTAKE_AND_HTTPS_ROUTE_READY')
except BaseException:
 atomic(gate,old_gate,0o755)
 atomic(conf,old_conf,stat.S_IMODE(conf.stat().st_mode))
 subprocess.run(['nginx','-t'],check=True)
 subprocess.run(['systemctl','reload','nginx'],check=True)
 if receiver.exists():receiver.unlink()
 for p in [base/'files',base/'receipts',base]:
  if p.exists():p.rmdir()
 raise
PY
