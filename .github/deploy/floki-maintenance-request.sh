#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import os,stat,json,hashlib,zipfile,io,pathlib,subprocess,urllib.request,urllib.error,grp,time,re
P=pathlib.Path
build='a1c19b812ef5ebdfd19500d3721b2b29750deca7'
version='0.4.89'
name='celikom-extension-'+version+'.zip'
spool_root=P('/srv/celikom/ci-runner/runner/celikom-build-spool')
def read_regular(p,limit):
 for parent in [p,*p.parents]:
  st=parent.lstat()
  assert not stat.S_ISLNK(st.st_mode), 'SYMLINK_REFUSED '+str(parent)
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  st=os.fstat(fd)
  assert stat.S_ISREG(st.st_mode) and 0<st.st_size<=limit, 'INVALID_REGULAR_FILE '+str(p)
  with os.fdopen(fd,'rb',closefd=False) as f: data=f.read(limit+1)
  assert len(data)==st.st_size, 'INVALID_FILE_SIZE '+str(p)
  return data
 finally: os.close(fd)
def find_candidates():
 if not spool_root.exists(): return []
 root=spool_root.lstat()
 assert stat.S_ISDIR(root.st_mode) and not stat.S_ISLNK(root.st_mode), 'UNSAFE_SPOOL_ROOT'
 found=[]
 for directory in spool_root.iterdir():
  if not directory.name.startswith(build+'-'): continue
  st=directory.lstat()
  assert stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode), 'UNSAFE_SPOOL_ENTRY'
  receipt=json.loads(read_regular(directory/'receipt.json',16384))
  assert receipt.get('schema')==1 and receipt.get('state')=='private-unreleased-ci'
  assert receipt.get('sha')==build
  assert re.fullmatch(r'[1-9][0-9]{0,19}',str(receipt.get('runId','')))
  assert re.fullmatch(r'[1-9][0-9]{0,19}',str(receipt.get('attempt','')))
  files=receipt.get('files')
  assert isinstance(files,list) and len(files)==1
  item=files[0]
  assert item.get('kind')=='extension' and item.get('name')==name
  assert isinstance(item.get('bytes'),int) and 0<item['bytes']<=64*1024*1024
  assert re.fullmatch(r'[a-f0-9]{64}',str(item.get('sha256','')))
  data=read_regular(directory/name,64*1024*1024)
  digest=hashlib.sha256(data).hexdigest()
  assert len(data)==item['bytes'] and digest==item['sha256'], 'SPOOL_PACKAGE_IDENTITY_MISMATCH'
  assert read_regular(directory/(name+'.sha256'),256).decode()==digest+'  '+name+'\n'
  found.append((receipt,directory,data,digest))
 return found
deadline=time.monotonic()+240
candidates=[]
while time.monotonic()<deadline:
 candidates=find_candidates()
 if candidates: break
 time.sleep(5)
assert candidates, 'EXTENSION_SPOOL_NOT_FOUND_FOR_PINNED_BUILD'
digests={x[3] for x in candidates}
sizes={len(x[2]) for x in candidates}
assert len(digests)==1 and len(sizes)==1, 'MULTIPLE_DIFFERENT_BUILDS_FOR_SAME_SOURCE'
receipt,spool,data,sha=max(candidates,key=lambda x:(int(x[0]['runId']),int(x[0]['attempt'])))
assert data[:4]==bytes.fromhex('504b0304'), 'INVALID_ZIP_HEADER'
with zipfile.ZipFile(io.BytesIO(data)) as z:
 infos=z.infolist()
 names=[x.filename for x in infos]
 assert len(names)==len(set(names)), 'DUPLICATE_ZIP_ENTRY'
 assert sum(x.file_size for x in infos)<=64*1024*1024, 'ZIP_UNPACKED_SIZE_LIMIT'
 for x in infos:
  q=P(x.filename)
  assert not q.is_absolute() and '..' not in q.parts and '\\' not in x.filename, 'UNSAFE_ZIP_PATH'
  assert not stat.S_ISLNK(x.external_attr>>16), 'ZIP_SYMLINK_REFUSED'
 assert z.testzip() is None, 'ZIP_CRC_FAILURE'
 manifest=json.loads(z.read('manifest.json'))
 config=json.loads(z.read('api/config.json'))
 assert manifest.get('version')==version, 'MANIFEST_VERSION_MISMATCH'
 assert sorted(manifest.get('host_permissions',[]))==['https://api.celikom.com/*','https://music.yandex.ru/*'], 'HOST_PERMISSION_MISMATCH'
 assert 'update_url' not in manifest, 'UNEXPECTED_UPDATE_URL'
 assert config.get('baseUrl')=='https://api.celikom.com', 'API_ORIGIN_MISMATCH'
print('EXTENSION_SPOOL_INDEPENDENT_VALIDATION_PASS')
print('EXTENSION_SOURCE_SHA',build)
print('EXTENSION_BUILD_RUN',receipt['runId'],'ATTEMPT',receipt['attempt'])
print('EXTENSION_PACKAGE',name,'BYTES',len(data),'SHA256',sha)
gid=grp.getgrnam('www-data').gr_gid
def trusted_dir(p):
 for a in [p,*p.parents]:
  s=a.lstat()
  assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not(s.st_mode&0o022), 'UNTRUSTED_RELEASE_DIRECTORY '+str(a)
def immutable(p,b):
 trusted_dir(p.parent)
 if p.exists():
  assert read_regular(p,len(b)+1)==b, 'IMMUTABLE_RELEASE_COLLISION '+str(p)
 else:
  fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o640)
  with os.fdopen(fd,'wb') as f:
   f.write(b);f.flush();os.fsync(f.fileno())
 os.chown(p,0,gid);os.chmod(p,0o640)
for directory in ['/srv/celikom-releases/private/extension','/srv/celikom-releases/owner-downloads']:
 p=P(directory)/name
 immutable(p,data)
 immutable(P(str(p)+'.sha256'),(sha+'  '+name+'\n').encode())
 if directory.endswith('owner-downloads'):
  subprocess.run(['runuser','-u','www-data','--','test','-r',str(p)],check=True)
 print('IMMUTABLE_EXTENSION_COPY_PASS',str(p),sha)
conf=P('/etc/nginx/sites-available/celikom-site-https')
old=read_regular(conf,131072).decode()
assert 'auth_basic "CELIKOM private review";' in old
assert 'auth_basic_user_file /etc/nginx/celikom-site.htpasswd;' in old
needle='    location = /downloads/extension/celikom-extension-0.4.73.zip {'
assert old.count(needle)==1, 'KNOWN_OWNER_ROUTE_ANCHOR_MISMATCH'
start=old.index(needle);cursor=start+len(needle);depth=1
while depth:
 assert cursor<len(old), 'NGINX_BLOCK_UNTERMINATED'
 if old[cursor]=='{':depth+=1
 elif old[cursor]=='}':depth-=1
 cursor+=1
oldblock=old[start:cursor]
newblock=oldblock.replace('0.4.73',version)
assert 'auth_basic off' not in newblock and name in newblock, 'OWNER_ROUTE_AUTH_OR_ALIAS_MISMATCH'
url_path='/downloads/extension/'+name
if url_path not in old:
 new=old.replace(oldblock,oldblock+'\n\n'+newblock)
 backup=P('/root/celikom-extension-0489-nginx-before.conf')
 if not backup.exists():
  fd=os.open(backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as f:f.write(old.encode());f.flush();os.fsync(f.fileno())
 st=conf.lstat()
 assert stat.S_ISREG(st.st_mode) and st.st_uid==0, 'NGINX_CONFIG_OWNERSHIP_MISMATCH'
 tmp=conf.with_name(conf.name+'.celikom-0489.tmp')
 fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,st.st_mode&0o777)
 try:
  with os.fdopen(fd,'w') as f:f.write(new);f.flush();os.fsync(f.fileno())
  os.chown(tmp,st.st_uid,st.st_gid);os.chmod(tmp,st.st_mode&0o777)
  os.replace(tmp,conf)
  subprocess.run(['nginx','-t'],check=True)
  subprocess.run(['systemctl','reload','nginx'],check=True)
 except BaseException:
  try:tmp.unlink()
  except FileNotFoundError:pass
  conf.write_text(old)
  subprocess.run(['nginx','-t'],check=True)
  subprocess.run(['systemctl','reload','nginx'],check=True)
  raise
else:
 assert newblock in old, 'EXISTING_OWNER_ROUTE_DIFFERS'
for url in ['https://celikom.com'+url_path,'https://celikom.com/downloads/extension/celikom-extension-0.4.73.zip']:
 try:r=urllib.request.urlopen(url,timeout=20)
 except urllib.error.HTTPError as e:r=e
 assert r.status==401 and 'Basic' in r.headers.get('WWW-Authenticate',''), 'OWNER_DOWNLOAD_BASIC_GATE_FAILED '+url
 print('OWNER_DOWNLOAD_BASIC_GATE_PASS',url)
for url in ['https://api.celikom.com/api/v1/health','https://api.celikom.com/api/v1/config']:
 with urllib.request.urlopen(url,timeout=20) as r:
  assert r.status==200 and 'application/json' in r.headers.get('Content-Type',''), 'API_HEALTH_CHECK_FAILED '+url
print('EXTENSION_0489_PRIVATE_OWNER_DOWNLOAD_READY')
print('OWNER_DOWNLOAD_URL','https://celikom.com'+url_path)
print('EXTENSION_SHA256',sha)
print('EXTENSION_BYTES',len(data))
PY