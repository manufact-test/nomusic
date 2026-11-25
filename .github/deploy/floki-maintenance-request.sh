#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import os,sys,hashlib,json,subprocess,datetime,urllib.request,urllib.error
from pathlib import Path
root=Path('/srv/celikom-releases/windows/stable')
cur=root/'current'
expected='0.24.55'
def check(cond,code):
 if not cond: raise RuntimeError(code)
check(cur.is_symlink() and os.readlink(cur)=='versions/'+expected,'WINDOWS_CURRENT_POINTER_MISMATCH')
vdir=cur
manifest=vdir/'manifest.json'
signature=vdir/'manifest.json.sig'
installer=vdir/('CELIKOM-Windows-'+expected+'.exe')
key=Path('/root/celikom-secrets/windows-stable-public.der')
for p in (manifest,signature,installer,key):
 check(p.is_file(),'WINDOWS_FILE_MISSING_'+p.name)
check(64<=signature.stat().st_size<=80,'WINDOWS_SIGNATURE_SIZE_INVALID')
check(hashlib.sha256(key.read_bytes()).hexdigest()=='46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95','WINDOWS_PUBLIC_PIN_MISMATCH')
verify=subprocess.run(['openssl','dgst','-sha256','-verify',str(key),'-keyform','DER','-signature',str(signature),str(manifest)],capture_output=True,text=True,timeout=15)
check(verify.returncode==0,'WINDOWS_MANIFEST_SIGNATURE_INVALID')
data=json.loads(manifest.read_text('utf8'))
check(data.get('schema')==2 and data.get('version')==expected and data.get('sequence')==2,'WINDOWS_MANIFEST_IDENTITY_INVALID')
check(data.get('channel')=='stable' and data.get('publisher')=='CELIKOM','WINDOWS_MANIFEST_CHANNEL_INVALID')
expected_url='https://celikom.com/CELIKOM/Windows/Updates/stable/'+expected+'/CELIKOM-Windows-'+expected+'.exe'
check(data.get('packageUrl')==expected_url,'WINDOWS_MANIFEST_PACKAGE_URL_INVALID')
expiry=datetime.datetime.fromisoformat(data['expiresAt'].replace('Z','+00:00'))
now=datetime.datetime.now(datetime.timezone.utc)
check(expiry>now,'WINDOWS_MANIFEST_EXPIRED')
check(installer.stat().st_size==data['packageSize'],'WINDOWS_EXE_SIZE_MISMATCH')
digest=hashlib.sha256(installer.read_bytes()).hexdigest()
check(digest==data['sha256']=='f4c9a7881164ac7a9b5681d9f3568e5cbd3a9915c9e1da7b475caa20d3fb6487','WINDOWS_EXE_HASH_MISMATCH')
check(installer.open('rb').read(2)==b'MZ','WINDOWS_EXE_PE_HEADER_INVALID')
print('WINDOWS_RELEASE_LOCAL_SIGNED_P256_OK','version='+expected,'sequence=2','sha256='+digest,'size='+str(installer.stat().st_size),'expiresAt='+data['expiresAt'])
print('WINDOWS_MANIFEST_VALID_FOR_HOURS',round((expiry-now).total_seconds()/3600,1))
def probe(hostpath):
 try:
  req=urllib.request.Request(hostpath,headers={'User-Agent':'CELIKOM-Windows-ReadOnly-Owner-Audit'})
  with urllib.request.urlopen(req,timeout=18) as response:
   code=response.status
 except urllib.error.HTTPError as e:
  code=e.code
 return code
expected_responses={
 'https://api.celikom.com/api/v1/health':{200},
 'https://api.celikom.com/api/v1/config':{200},
 'https://api.celikom.com/api/v1/auth/me':{401},
 'https://api.celikom.com/api/v1/entitlement':{401},
 'https://api.celikom.com/api/v1/resolve?service=yandex&track_id=144530503':{401},
 'https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.55.exe':{401},
 'https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json':{401},
 'https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json.sig':{401},
 'https://celikom.com/CELIKOM/Windows/Updates/stable/0.24.55/manifest.json':{401}
}
for url,allowed in expected_responses.items():
 status=probe(url)
 print('WINDOWS_HTTP',url,status)
 check(status in allowed,'WINDOWS_HTTP_UNEXPECTED_'+str(status))
result=subprocess.run(['nginx','-t'],capture_output=True,text=True,timeout=15)
check(result.returncode==0,'WINDOWS_NGINX_SYNTAX_INVALID')
print('WINDOWS_FLOKI_READONLY_AUDIT_PASS')
PY
