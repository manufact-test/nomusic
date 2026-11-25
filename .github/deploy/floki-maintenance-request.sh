#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import hashlib,json,zipfile,pathlib,urllib.request,urllib.error
root=pathlib.Path('/srv/celikom/app/staging-20261122')
p=pathlib.Path('/srv/celikom-releases/private/extension/celikom-extension-0.4.73.zip')
b=p.read_bytes()
assert hashlib.sha256(b).hexdigest()=='968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb'
with zipfile.ZipFile(p) as z:
 c=json.loads(z.read('api/config.json'));m=json.loads(z.read('manifest.json'))
 print('EXTENSION_PACKAGE',json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'size':len(b),'config':c,'version':m['version'],'hosts':m['host_permissions'],'update_url':m.get('update_url')}))
for path in ['/api/v1/health','/api/v1/config','/api/v1/auth/me','/api/v1/entitlement']:
 try:
  res=urllib.request.urlopen('https://api.celikom.com'+path,timeout=20)
 except urllib.error.HTTPError as e: res=e
 data=res.read(32000)
 print('HTTP_PROBE',path,res.status,res.headers.get('Content-Type'),data.decode('utf8')[:8000])
for name in ['src/Auth/AuthService.php','src/Entitlement/EntitlementService.php']:
 q=root/name
 if q.is_file():
  import base64
  print('SOURCE_BEGIN:'+name)
  print(base64.b64encode(q.read_bytes()).decode())
  print('SOURCE_END:'+name)
print('EXTENSION_FLOKI_READONLY_AUDIT_PASS')
PY
