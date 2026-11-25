#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
from pathlib import Path
for p in Path('/etc/nginx/sites-enabled').iterdir():
 text=p.read_text()
 if 'celikom.com' not in text: continue
 print('NGINX_SITE',str(p.resolve()))
 for line in text.splitlines():
  if any(s in line for s in ['server_name','location','alias','auth_basic','include','proxy_pass','root ']): print(line)
print('EXTENSION_NGINX_AUDIT_PASS')
PY
