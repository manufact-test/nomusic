#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import hashlib,pathlib,urllib.request,urllib.error
p=pathlib.Path('/srv/celikom/app/staging-20261122/src/Application.php')
print('LIVE_APPLICATION_SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
for origin in ['chrome-extension://abcdefghijklmnopabcdefghijklmnop','https://music.yandex.ru','https://untrusted.example']:
 q=urllib.request.Request('https://api.celikom.com/api/v1/auth/me',method='OPTIONS',headers={'Origin':origin,'Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'authorization'})
 try:r=urllib.request.urlopen(q,timeout=20)
 except urllib.error.HTTPError as e:r=e
 print('PREFLIGHT',origin,r.status,r.headers.get('Access-Control-Allow-Origin'),r.headers.get('Access-Control-Allow-Headers'))
print('EXTENSION_CORS_BASELINE_AUDIT_COMPLETE')
PY
