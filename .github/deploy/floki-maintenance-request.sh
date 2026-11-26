#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import pathlib, subprocess, re, collections
P=pathlib.Path
prefix='3ec3c4ab'
paths=set()
for pattern in ['/var/log/php*log','/var/log/php*/*.log','/var/log/nginx/*error*.log','/srv/celikom/shared/*error*.log','/srv/celikom/logs/*.log']:
 paths.update(P('/').glob(pattern.lstrip('/')))
sources=[]
for p in sorted(paths):
 try:
  if not p.is_file() or p.is_symlink():continue
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-4*1024*1024))
   sources.append((p.name,f.read().decode('utf-8','replace')))
 except OSError: pass
r=subprocess.run(['journalctl','-u','php8.3-fpm','-u','nginx','--since','-2 hours','--no-pager','-o','cat','-n','3000'],capture_output=True,text=True,timeout=20)
sources.append(('service-journal',r.stdout))
found=set()
for name,body in sources:
 for m in re.finditer(r'CELIKOM upload_attempt=([a-f0-9-]{36}) status=(\d+) elapsed_ms=(\d+)',body,re.I):
  if m[1].lower().startswith(prefix):
   record=(m[1].lower(),m[2],m[3])
   if record not in found:print('MATCHED_UPLOAD_ATTEMPT',*record);found.add(record)
 codes=collections.Counter(re.findall(r'CELIKOM service_unavailable(?:_sqlstate_[A-Z0-9]+_driver_[0-9]+)?',body))
 if codes:print('SERVICE_ERROR_CODE_COUNTS',name,dict(codes))
 limits=sum(1 for line in body.splitlines() if '/api/v1/uploads' in line and 'too large body' in line)
 if limits:print('UPLOAD_BODY_LIMIT_ERRORS',name,limits)
print('TARGET_ATTEMPT_MATCHES',len(found))
for path in ['/etc/nginx/sites-available/celikom-api-https','/etc/nginx/sites-available/celikom-api-staging']:
 p=P(path)
 if p.is_file():
  for line in p.read_text().splitlines():
   if any(key in line for key in ['upload_max_filesize','post_max_size','client_max_body_size']):print('CONFIG_UPLOAD_LIMIT',line.strip())
print('UPLOAD_READONLY_ATTEMPT_AUDIT_DONE')
PY
