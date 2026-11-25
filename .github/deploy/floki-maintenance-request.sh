#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Produce owner-private Android v95 route candidate. Nothing public changes.
in=/root/celikom-cutover-prepared/android-updates.conf
out=/root/celikom-cutover-prepared/android-updates-v95.conf
apk=/srv/celikom-releases/private/android-v95/CELIKOM-Android-0.3.94-SIGNED.apk
manifest=/srv/celikom-releases/private/android-v95/stable-floki-candidate.json
[[ -f "$in" && ! -L "$in" && -f "$apk" && ! -L "$apk" && -f "$manifest" && ! -L "$manifest" ]]
printf '%s  %s\n' \
 d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469 "$apk" \
 8e5205b64ea65b8a9879b7034a3e5c141a8e96b79a0e1a07c1d849def358478e "$manifest" | sha256sum -c --status
[[ ! -e "$out" && ! -L "$out" ]]
python3 - "$in" "$out" <<'PY'
import pathlib,re,sys
inp=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2])
s=inp.read_text()
old='93-5ceb9db20d47390e88cd316c3f74c1928534b35bc54e316f5b841f49b951ff6a.apk'
new='95-d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469.apk'
assert s.count(old)==2
assert s.count('auth_basic off;')==2
assert s.count('limit_except GET HEAD { deny all; }')==2
assert 'location = /updates/android/stable.json' in s
assert 'alias /srv/celikom-releases/public/android/updates/android/stable.json;' in s
v=s.replace(old,new).replace('Prepared only; do not include until API/client acceptance and owner approval.',
                             'Prepared v95 only; do not include or publish until owner acceptance and final safety gate.')
names=re.findall(r'(?m)^\s*location\s*=\s*(\S+)\s*\{',v)
assert names==['/updates/android/stable.json','/releases/android/'+new]
assert re.sub(re.escape(new),old,v).replace(
 'Prepared v95 only; do not include or publish until owner acceptance and final safety gate.',
 'Prepared only; do not include until API/client acceptance and owner approval.')==s
out.write_text(v)
out.chmod(0o600)
print('ANDROID_V95_EXACT_NGINX_TWO_LOCATION_DIFF_VALIDATED')
PY
test -f "$out" && test "$(stat -c '%u:%a' "$out")" = 0:600
test -f /etc/nginx/nginx.conf
test -f /etc/nginx/sites-available/celikom-site-https
# The new fragment is not included in the live Nginx configuration.
! grep -R -Fq '/root/celikom-cutover-prepared/android-updates-v95.conf' /etc/nginx/sites-enabled /etc/nginx/sites-available
tmp=$(mktemp /root/celikom-android-v95-test-nginx-XXXXXXXX)
trap 'rm -f -- "$tmp"' EXIT
cat > "$tmp" <<EOF
worker_processes 1;
error_log /dev/null warn;
pid /tmp/celikom-v95-nginx-validation.pid;
events { worker_connections 64; }
http {
 server {
  listen 127.0.0.1:19999;
  server_name private-test.invalid;
  include $out;
 }
}
EOF
nginx -t -c "$tmp" -p /etc/nginx
nginx -t
test "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' https://celikom.com/updates/android/stable.json)" = 401
echo CELIKOM_ANDROID_V95_PRIVATE_NGINX_CANDIDATE_READY_NOT_PUBLISHED
