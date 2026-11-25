#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import os,stat,json,hashlib,zipfile,io,pathlib,re,subprocess,urllib.request,urllib.error,grp
P=pathlib.Path
name='celikom-extension-0.4.81.zip'
sha='9ddf20fef3c597eb8e91af7c51a4938fde85df792923473c934fe53e258b2380'
build='4cc7814454111f89eb5fe779e5093e6ab584a71d'
run='45656926920'
spool=P('/srv/celikom/ci-runner/runner/celikom-build-spool')/(build+'-'+run+'-1')
def read_regular(p,limit):
 for parent in [p,*p.parents]:
  assert not parent.is_symlink(), 'SYMLINK_REFUSED'
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  st=os.fstat(fd);assert stat.S_ISREG(st.st_mode) and 0<st.st_size<=limit
  with os.fdopen(fd,'rb',closefd=False) as f: data=f.read(limit+1)
  assert len(data)==st.st_size
  return data
 finally:os.close(fd)
receipt=json.loads(read_regular(spool/'receipt.json',16384))
assert receipt['schema']==1 and receipt['state']=='private-unreleased-ci'
assert receipt['sha']==build and receipt['runId']==run and receipt['attempt']=='1'
assert receipt['files']==[{'kind':'extension','name':name,'bytes':2491245,'sha256':sha}]
data=read_regular(spool/name,64*1024*1024)
assert len(data)==2491245 and hashlib.sha256(data).hexdigest()==sha
assert read_regular(spool/(name+'.sha256'),256).decode()==sha+'  '+name+'\n'
with zipfile.ZipFile(io.BytesIO(data)) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 assert sum(x.file_size for x in z.infolist())<64*1024*1024
 for x in z.infolist():
  q=P(x.filename)
  assert not q.is_absolute() and '..' not in q.parts and '\\' not in x.filename
  assert not stat.S_ISLNK(x.external_attr>>16)
 assert json.loads(z.read('api/config.json'))['baseUrl']=='https://api.celikom.com'
 m=json.loads(z.read('manifest.json'))
 assert m['version']=='0.4.81'
 assert sorted(m['host_permissions'])==['https://api.celikom.com/*','https://music.yandex.ru/*']
 assert 'update_url' not in m
 assert z.testzip() is None
print('EXTENSION_SPOOL_INDEPENDENT_VALIDATION_PASS')
gid=grp.getgrnam('www-data').gr_gid
def trusted_dir(p):
 for a in [p,*p.parents]:
  s=a.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not(s.st_mode&0o022),str(a)
def immutable(p,b):
 trusted_dir(p.parent)
 if p.exists():assert read_regular(p,len(b)+1)==b
 else:
  fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o640)
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 os.chown(p,0,gid);os.chmod(p,0o640)
for directory in ['/srv/celikom-releases/private/extension','/srv/celikom-releases/owner-downloads']:
 p=P(directory)/name
 immutable(p,data);immutable(P(str(p)+'.sha256'),(sha+'  '+name+'\n').encode())
 subprocess.run(['runuser','-u','www-data','--','test','-r',str(p)],check=True) if directory.endswith('owner-downloads') else None
 print('IMMUTABLE_EXTENSION_COPY_PASS',str(p),sha)
conf=P('/etc/nginx/sites-available/celikom-site-https')
old=read_regular(conf,131072).decode()
assert 'auth_basic "CELIKOM private review";' in old and 'auth_basic_user_file /etc/nginx/celikom-site.htpasswd;' in old
needle='    location = /downloads/extension/celikom-extension-0.4.73.zip {'
assert old.count(needle)==1
start=old.index(needle); cursor=start+len(needle); depth=1
while depth:
 assert cursor<len(old)
 if old[cursor]=='{':depth+=1
 elif old[cursor]=='}':depth-=1
 cursor+=1
blocks=[old[start:cursor]]
newblock=blocks[0].replace('0.4.73','0.4.81')
assert 'auth_basic off' not in newblock
if '/downloads/extension/'+name not in old:
 new=old.replace(blocks[0],blocks[0]+'\n\n'+newblock)
 backup=P('/root/celikom-extension-0481-nginx-before.conf')
 if not backup.exists():backup.write_text(old);os.chmod(backup,0o600)
 try:
  conf.write_text(new)
  subprocess.run(['nginx','-t'],check=True)
  subprocess.run(['systemctl','reload','nginx'],check=True)
 except BaseException:
  conf.write_text(old);subprocess.run(['nginx','-t'],check=True);subprocess.run(['systemctl','reload','nginx'],check=True);raise
else: assert newblock in old
for url in ['https://celikom.com/downloads/extension/'+name,'https://celikom.com/downloads/extension/celikom-extension-0.4.73.zip']:
 try:r=urllib.request.urlopen(url,timeout=20)
 except urllib.error.HTTPError as e:r=e
 assert r.status==401 and 'Basic' in r.headers.get('WWW-Authenticate','')
 print('OWNER_DOWNLOAD_BASIC_GATE_PASS',url)
for url in ['https://api.celikom.com/api/v1/health','https://api.celikom.com/api/v1/config']:
 with urllib.request.urlopen(url,timeout=20) as r:assert r.status==200 and 'application/json' in r.headers.get('Content-Type','')
print('EXTENSION_0481_PRIVATE_OWNER_DOWNLOAD_READY')
PY
