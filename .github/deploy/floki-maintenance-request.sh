#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# API-only FastCGI runtime limits; no global PHP pool or public routing changes.
live=$(readlink -f /etc/nginx/sites-enabled/celikom-api-staging)
candidate=/root/celikom-cutover-prepared/api-staging.conf
app=/srv/celikom/app/staging-20261122
[[ "$live" == /etc/nginx/sites-available/* && -f "$live" && -f "$candidate" ]]
backup=$(mktemp -d /root/celikom-api-fpm-backup-XXXXXXXX)
cp -a "$live" "$backup/live"
cp -a "$candidate" "$backup/candidate"
probe=$(mktemp "$app/.fpm-upload-probe-XXXXXXXX.php")
tmp=$(mktemp -d)
ok=0
cleanup(){
  rc=$?
  rm -f "$probe"
  rm -rf "$tmp"
  if [[ "$ok" != 1 ]]; then
    cp -a "$backup/live" "$live"
    cp -a "$backup/candidate" "$candidate"
    nginx -t && systemctl reload nginx || true
    echo CELIKOM_API_UPLOAD_ROLLBACK
  fi
  exit "$rc"
}
trap cleanup EXIT
cat > "$probe" <<'PHP'
<?php
header('Content-Type: application/json');
echo json_encode(['upload'=>ini_get('upload_max_filesize'),'post'=>ini_get('post_max_size'),'execution'=>ini_get('max_execution_time'),'error'=>$_FILES['file']['error']??-1,'size'=>$_FILES['file']['size']??0,'actual'=>isset($_FILES['file']['tmp_name'])&&is_uploaded_file($_FILES['file']['tmp_name'])?filesize($_FILES['file']['tmp_name']):0]);
PHP
chmod 644 "$probe"
python3 - "$live" "$candidate" "$probe" "$backup" <<'PY'
import pathlib,re,sys
live,candidate,probe,backup=map(pathlib.Path,sys.argv[1:])
param=r'fastcgi_param PHP_ADMIN_VALUE "upload_max_filesize=30M\npost_max_size=32M\nmax_execution_time=120";'
for p in (live,candidate):
    assert p.stat().st_uid==0
    s=p.read_text()
    assert 'listen 127.0.0.1:8081;' in s
    assert 'PHP_ADMIN_VALUE' not in s and 'PHP_VALUE' not in s
    anchor='fastcgi_param SCRIPT_FILENAME $document_root/index.php;'
    assert s.count(anchor)==1
    s=s.replace(anchor,anchor+'\n        '+param)
    s,n=re.subn(r'client_max_body_size (?:1m|32m);','client_max_body_size 32m;',s)
    assert n==1
    p.write_text(s)
s=live.read_text()
passes=re.findall(r'^\s*fastcgi_pass\s+([^;\n]+);',s,re.M)
assert len(passes)==1 and re.fullmatch(r'unix:/run/php/[A-Za-z0-9_.-]+\.sock|127\.0\.0\.1:\d+',passes[0])
(backup/'live-final').write_text(s)
# A disposable loopback-only HTTP listener using the exact API FastCGI socket and limits.
extra='\nserver {\n    listen 127.0.0.1:18081;\n    server_name localhost;\n    access_log off;\n    client_max_body_size 32m;\n    location = /probe {\n        include fastcgi_params;\n        fastcgi_param SCRIPT_FILENAME '+str(probe)+';\n        '+param+'\n        fastcgi_pass '+passes[0]+';\n        fastcgi_read_timeout 120s;\n    }\n    location / { return 404; }\n}\n'
assert not re.search(r'listen\s+[^;]*18081',s)
live.write_text(s+extra)
PY
nginx -t
systemctl reload nginx
for i in $(seq 1 20); do
  if curl -fsS --max-time 3 http://127.0.0.1:18081/probe > /dev/null; then break; fi
  sleep 1
done
truncate -s 31457280 "$tmp/upload.bin"
curl --fail --silent --show-error --max-time 120 -F "file=@$tmp/upload.bin" http://127.0.0.1:18081/probe > "$tmp/result.json"
python3 - "$tmp/result.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
assert v=={'upload':'30M','post':'32M','execution':'120','error':0,'size':31457280,'actual':31457280},v
print('API_FPM_HTTP_30M_UPLOAD_OK',v)
PY
cat "$backup/live-final" > "$live"
nginx -t
systemctl reload nginx
for i in $(seq 1 15); do
  if [[ "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 https://api.celikom.com/api/v1/health)" == 200 && "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 https://api.celikom.com/admin/)" == 404 ]]; then
    ok=1
    break
  fi
  sleep 1
done
[[ "$ok" == 1 ]]
echo "API_FPM_BACKUP $backup"
echo CELIKOM_API_UPLOAD_LIMITS_VERIFIED
