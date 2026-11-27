#!/bin/bash
set -Eeuo pipefail
# Bounded read-only upload transport audit; never print raw requests or IPs.
python3 <<'PY'
from pathlib import Path
import re,json,subprocess
attempts={"2ec18523-31dd-444c-a9ba-d2c96bc8467e","bce744e7-0000-0000-0000-000000000000","0849c933-ef2a-4569-875f-859c8801a40a","c0d206a3-efa1-40fb-b082-21017ccfcc35"}
prefixes={"2ec18523","bce744e7","0849c933","c0d206a3"}
ng=subprocess.run(["nginx","-T"],capture_output=True,text=True,timeout=15)
paths=set()
for line in ng.stdout.splitlines():
 m=re.match(r"\s*(access_log|error_log)\s+(/[^;\s]+)",line)
 if m:paths.add(m[2])
 for key in ["client_body_timeout","client_body_buffer_size","client_max_body_size","client_body_temp_path"]:
  if re.match(r"\s*"+key+r"\s+",line):print("UPLOAD_DIRECTIVE",line.strip())
paths.update(str(p) for p in Path("/var/log").glob("php*fpm*.log"))
for name in sorted(paths)[:30]:
 p=Path(name)
 if not p.is_file() or p.is_symlink():continue
 with p.open("rb") as f:
  f.seek(max(0,p.stat().st_size-8*1024*1024));s=f.read().decode("utf-8","replace")
 count=0
 for line in s.splitlines():
  u=re.search(r"upload_attempt=([a-f0-9-]{36}) status=(\d+) elapsed_ms=(\d+)",line,re.I)
  if u and u[1][:8].lower() in prefixes:
   print("UPLOAD_APPLICATION",json.dumps({"attempt":u[1][:8],"status":int(u[2]),"elapsed_ms":int(u[3])}));count+=1
  relevant=bool(re.search(r"(?:27/Nov/2026:20:(?:04|05|28|29):|2026/11/27 20:(?:04|05|28|29):)",line)) and "/api/v1/uploads" in line
  if not relevant:continue
  a=re.search(r'\[([^\]]+)\].*?"(?:POST|OPTIONS) /api/v1/uploads[^"]*" (\d{3}) (\d+)',line)
  if a:
   proto=re.search(r"HTTP/([0-9.]+)",line)
   print("UPLOAD_NGINX",json.dumps({"at":a[1],"status":int(a[2]),"response_bytes":int(a[3]),"http":proto[1] if proto else None}));count+=1
  for token in ["client timed out","client prematurely closed connection","upstream timed out","while reading client request body","No space left","Permission denied"]:
   if token in line:print("UPLOAD_NGINX_ERROR",json.dumps({"category":token,"at":line[:19]}));count+=1
 if count:print("UPLOAD_AUDIT_LOG_MATCHES",p.name,count)
print("UPLOAD_TRANSPORT_AUDIT_READONLY_DONE")
PY
