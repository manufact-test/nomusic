#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import os,pathlib,hashlib,subprocess,urllib.request,urllib.error,re,time
P=pathlib.Path
p=P('/srv/celikom/app/staging-20261122/src/Application.php')
assert not p.is_symlink()
old=p.read_bytes()
expected='ca2a855e6da8b56174130a50cf277b9778600830627bf1b2250192b19152418a'
if hashlib.sha256(old).hexdigest()==expected:
 text=old.decode()
 target="|| self::isNativeAudioOrigin($method, $path, $headers['origin'] ?? '')"
 assert text.count(target)==2 and 'function isExtensionApiOrigin' not in text
 text=text.replace(target,target+"\n            || self::isExtensionApiOrigin($method, $path, $headers['origin'] ?? '')")
 text=text.replace("    private static function isNativeAudioOrigin","    // Unpacked Chrome/Brave installs have per-install IDs. CORS permits transport\n    // only: no cookies, credentials, account identity or entitlement is granted.\n    // Bearer/session and signed-audio validation remain mandatory on every route.\n    private static function isExtensionApiOrigin(string $method, string $path, string $origin): bool\n    {\n        return in_array($method, ['GET', 'HEAD', 'POST', 'OPTIONS'], true)\n            && str_starts_with($path, '/api/v1/')\n            && preg_match('~^chrome-extension://[a-p]{32}$~D', $origin) === 1;\n    }\n\n"+"    private static function isNativeAudioOrigin")
 new=text.encode()
else:new=old
assert hashlib.sha256(new).hexdigest()=='4f07e4b2026adfc7e742557d86fda2458a4dc28d5d5c9e3a9af54c0042422aac'
assert hashlib.sha256(old).hexdigest() in [expected,hashlib.sha256(new).hexdigest()]
# Application.php contains source only; repair the umask-restricted file from the prior atomic replace.
os.chmod(p,0o644)
backup=P('/root/celikom-extension-cors-20261125')
backup.mkdir(mode=0o700,exist_ok=True)
assert backup.lstat().st_uid==0 and not(backup.lstat().st_mode&0o077)
if not (backup/'Application.php').exists():
 assert hashlib.sha256(old).hexdigest()==expected
 (backup/'Application.php').write_bytes(old);os.chmod(backup/'Application.php',0o600)
unit=subprocess.check_output(['systemctl','list-units','--type=service','--state=active','--no-legend','php*-fpm.service'],text=True).split()
services=[x for x in unit if re.fullmatch(r'php[0-9]+\.[0-9]+-fpm\.service',x)]
assert len(services)==1
st=p.stat()
def replace(data):
 tmp=p.with_name('Application.php.extension-cors-tmp')
 fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,st.st_mode&0o777)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chown(tmp,st.st_uid,st.st_gid);os.chmod(tmp,0o644)
  subprocess.run(['php','-l',str(tmp)],check=True,stdout=subprocess.DEVNULL)
  os.replace(tmp,p)
 finally:
  if tmp.exists():tmp.unlink()
def fetch(path,method='GET',origin=None):
 headers={'Origin':origin} if origin else {}
 if method=='OPTIONS':headers.update({'Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'authorization,content-type,range'})
 try:return urllib.request.urlopen(urllib.request.Request('https://api.celikom.com'+path,method=method,headers=headers),timeout=20)
 except urllib.error.HTTPError as e:return e
try:
 if old!=new:replace(new);subprocess.run(['systemctl','reload',services[0]],check=True)
 origin='chrome-extension://abcdefghijklmnopabcdefghijklmnop'
 for path in ['/api/v1/auth/me','/api/v1/entitlement','/api/v1/resolve','/api/v1/uploads','/api/v1/audio/1']:
  r=fetch(path,'OPTIONS',origin)
  for attempt in range(8):
   if r.status==204 and r.headers.get('Access-Control-Allow-Origin')==origin:break
   print('PREFLIGHT_RELOAD_SETTLING',path,r.status,r.headers.get('Access-Control-Allow-Origin'))
   time.sleep(.5);r=fetch(path,'OPTIONS',origin)
  assert r.status==204 and r.headers.get('Access-Control-Allow-Origin')==origin
  assert not r.headers.get('Access-Control-Allow-Credentials')
  assert 'authorization' in r.headers.get('Access-Control-Allow-Headers','').lower()
  print('EXTENSION_PREFLIGHT_PASS',path)
 for path in ['/api/v1/auth/me','/api/v1/entitlement']:
  r=fetch(path,'GET',origin)
  assert r.status==401 and r.headers.get('Access-Control-Allow-Origin')==origin
  print('UNAUTHENTICATED_EXTENSION_STILL_DENIED_PASS',path)
 for bad in ['https://untrusted.example','null','chrome-extension://'+('z'*32),origin+'.evil']:
  assert fetch('/api/v1/auth/me','OPTIONS',bad).headers.get('Access-Control-Allow-Origin') is None
 for native in ['null','music-application://desktop','musicapplication://desktop']:
  assert fetch('/api/v1/audio/1','OPTIONS',native).headers.get('Access-Control-Allow-Origin')==native
  assert fetch('/api/v1/auth/me','OPTIONS',native).headers.get('Access-Control-Allow-Origin') is None
 for path in ['/api/v1/health','/api/v1/config']:assert fetch(path).status==200
 assert hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(new).hexdigest()
 print('EXTENSION_CORS_LIVE_PATCH_AND_BOUNDARIES_PASS')
except BaseException:
 if p.read_bytes()!=old:replace(old);subprocess.run(['systemctl','reload',services[0]],check=True)
 print('EXTENSION_CORS_AUTOMATIC_ROLLBACK');raise
PY

#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import os,stat,json,hashlib,zipfile,io,pathlib,re,subprocess,urllib.request,urllib.error,grp
P=pathlib.Path
name='celikom-extension-0.4.80.zip'
sha='e7304c49db0fdc2c11e5eeb4f1428bda796ddf44aca2729fa2d01520cf1481c0'
build='6c1b3491f790e4160464f75af722d64bf8521bc5'
run='45651329460'
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
assert receipt['files']==[{'kind':'extension','name':name,'bytes':2490430,'sha256':sha}]
data=read_regular(spool/name,64*1024*1024)
assert len(data)==2490430 and hashlib.sha256(data).hexdigest()==sha
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
 assert m['version']=='0.4.80'
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
newblock=blocks[0].replace('0.4.73','0.4.80')
assert 'auth_basic off' not in newblock
if '/downloads/extension/'+name not in old:
 new=old.replace(blocks[0],blocks[0]+'\n\n'+newblock)
 backup=P('/root/celikom-extension-0480-nginx-before.conf')
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
print('EXTENSION_0480_PRIVATE_OWNER_DOWNLOAD_READY')
PY
