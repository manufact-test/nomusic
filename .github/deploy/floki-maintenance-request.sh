#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import os,stat,json,hashlib,zipfile,io,pathlib,subprocess,urllib.request,urllib.error,grp,time,re
P=pathlib.Path
build='e52f819d6c69dc7e96734f60e14a17a92394b84c'
version='0.4.91'
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
deadline=time.monotonic()+45
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
print('EXTENSION_OWNER_PACKAGE_READONLY_VALIDATION_DONE')
PY
