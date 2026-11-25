#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import pathlib,hashlib,os,urllib.request,urllib.error,time
p=pathlib.Path('/srv/celikom/app/staging-20261122/src/Application.php')
assert not p.is_symlink()
assert hashlib.sha256(p.read_bytes()).hexdigest() in ['ca2a855e6da8b56174130a50cf277b9778600830627bf1b2250192b19152418a','4f07e4b2026adfc7e742557d86fda2458a4dc28d5d5c9e3a9af54c0042422aac']
os.chmod(p,0o644)
for attempt in range(10):
 try:
  r=urllib.request.urlopen('https://api.celikom.com/api/v1/health',timeout=10)
  if r.status==200:print('API_SOURCE_READABILITY_RECOVERED_HEALTH_200');break
 except urllib.error.HTTPError:time.sleep(.5)
else:raise RuntimeError('API_HEALTH_NOT_RECOVERED')
PY
