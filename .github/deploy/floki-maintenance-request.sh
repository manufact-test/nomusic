#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
python3 - <<'PY'
from pathlib import Path
from collections import Counter,deque
import re
logs=sorted(Path('/var/log/nginx').glob('*access*.log'))
print('LOG_FILE_COUNT',len(logs))
total=Counter(); endpoints=Counter()
for f in logs:
  if not f.is_file(): continue
  try:
    with f.open('r',encoding='utf-8',errors='ignore') as handle:
      tail=deque(handle,maxlen=30000)
  except PermissionError:
    continue
  samples=0
  for line in tail:
    if '/api/v1/' not in line or 'HTTP/' not in line: continue
    match=re.search(r'["]([A-Z]+) (/api/v1/[^ ?"]+)[^"]* HTTP/[^"]+["] (\d{3})',line)
    if not match: continue
    method,path,status=match.groups()
    if method not in ('GET','HEAD','POST','PUT','PATCH','DELETE'): continue
    # Only whitelisted endpoint groups, never query/user identifiers.
    if path.startswith('/api/v1/auth/'): group='/auth/*'
    elif path.startswith('/api/v1/audio/'): group='/audio/*'
    elif path.startswith('/api/v1/resolve'): group='/resolve'
    elif path.startswith('/api/v1/uploads'): group='/uploads'
    elif path.startswith('/api/v1/entitlement'): group='/entitlement'
    elif path.startswith('/api/v1/config'): group='/config'
    elif path.startswith('/api/v1/health'): group='/health'
    else: group='/other'
    key=(group,method,status)
    endpoints[key]+=1
    total[status]+=1
    samples+=1
  print('LOG_PARSED_API_ROWS',f.name,samples)
for (group,method,status),count in sorted(endpoints.items()):
 print('API_TRAFFIC_AGGREGATE',group,method,status,count)
print('API_TRAFFIC_HTTP5XX_TOTAL',sum(v for k,v in total.items() if k.startswith('5')))
print('API_TRAFFIC_ROWS_TOTAL',sum(total.values()))
PY
printf 'NGINX_RUNNING='; systemctl is-active nginx
printf 'PHP_RUNNING='; systemctl is-active php8.3-fpm
printf 'API_HEALTH='; curl -sS --max-time 10 -o /dev/null -w '%{http_code}\n' https://api.celikom.com/api/v1/health
printf 'NEW_MAIN_MIRROR_TIMER='; systemctl is-active celikom-mirror-sync.timer
echo CELIKOM_READONLY_LIVE_API_LOG_SUMMARY_COMPLETE
