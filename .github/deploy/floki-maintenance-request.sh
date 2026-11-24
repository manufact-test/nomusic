#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Stage the exact signed updater URL contract. Do NOT enable public feed.
prep=/root/celikom-cutover-prepared
snippet="$prep/windows-stable-locations.conf"
root=/srv/celikom-releases/windows/stable
test -d "$prep"
test "$(readlink "$root/current")" = versions/0.24.55
test ! -e "$snippet"
probe=/etc/nginx/conf.d/celikom-windows-feed-probe.conf
test ! -e "$probe"
tmp=$(mktemp -d /root/celikom-feed-http-XXXXXXXX)
ok=0
cleanup(){
  rc=$?
  rm -f "$probe"
  nginx -t && systemctl reload nginx || rc=1
  rm -rf "$tmp"
  if [[ "$ok" != 1 || "$rc" != 0 ]]; then rm -f "$snippet"; fi
  exit "$rc"
}
trap cleanup EXIT
cat > "$snippet" <<'NGINX'
    # Exact signed updater routes only. Integrate into the public TLS server
    # after owner acceptance; all other website paths retain Basic Auth.
    location = /CELIKOM/Windows/Updates/stable/latest.json {
        alias /srv/celikom-releases/windows/stable/current/manifest.json;
        auth_basic off;
        expires -1;
        default_type application/json;
        limit_except GET { deny all; }
    }
    location = /CELIKOM/Windows/Updates/stable/latest.json.sig {
        alias /srv/celikom-releases/windows/stable/current/manifest.json.sig;
        auth_basic off;
        expires -1;
        default_type application/octet-stream;
        limit_except GET { deny all; }
    }
    location ~ "^/CELIKOM/Windows/Updates/stable/(?<cwv>[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,5})/(?<cwm>manifest\.json(?:\.sig)?)$" {
        alias /srv/celikom-releases/windows/stable/versions/$cwv/$cwm;
        auth_basic off;
        limit_except GET { deny all; }
    }
    location ~ "^/CELIKOM/Windows/Updates/stable/(?<cwe>[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,5})/CELIKOM-Windows-(?P=cwe)\.exe$" {
        alias /srv/celikom-releases/windows/stable/versions/$cwe/CELIKOM-Windows-$cwe.exe;
        auth_basic off;
        default_type application/octet-stream;
        limit_except GET { deny all; }
    }
    location /CELIKOM/Windows/Updates/stable/ { return 404; }
NGINX
chmod 600 "$snippet"
{
  printf '%s\n' 'server {' '    listen 127.0.0.1:18083;' '    server_name localhost;' '    access_log off;'
  cat "$snippet"
  printf '%s\n' '    location / { return 404; }' '}'
} > "$probe"
nginx -t
systemctl reload nginx
base=http://127.0.0.1:18083/CELIKOM/Windows/Updates/stable
ready=0
for i in $(seq 1 15); do
  if curl -fsS --max-time 3 "$base/latest.json" > "$tmp/latest"; then ready=1; break; fi
  sleep 1
done
[[ "$ready" == 1 ]]
curl -fsS "$base/latest.json.sig" > "$tmp/sig"
cmp -s "$tmp/latest" "$root/current/manifest.json"
cmp -s "$tmp/sig" "$root/current/manifest.json.sig"
openssl dgst -sha256 -verify /root/celikom-secrets/windows-stable-public.der -keyform DER -signature "$tmp/sig" "$tmp/latest"
curl -fsS "$base/0.24.55/manifest.json" > "$tmp/version"
curl -fsS "$base/0.24.55/manifest.json.sig" > "$tmp/version.sig"
cmp -s "$tmp/latest" "$tmp/version"
cmp -s "$tmp/sig" "$tmp/version.sig"
status=$(curl -sS --max-time 15 -H 'Range: bytes=0-127' -o "$tmp/range" -w '%{http_code}' "$base/0.24.55/CELIKOM-Windows-0.24.55.exe")
[[ "$status" == 206 && "$(stat -c %s "$tmp/range")" == 128 ]]
head -c 128 "$root/current/CELIKOM-Windows-0.24.55.exe" > "$tmp/expected"
cmp -s "$tmp/range" "$tmp/expected"
for suffix in '' '0.24.55/' '0.24.55/CELIKOM-Windows-0.24.56.exe' '0.24.55/other.exe' 'private/extension/celikom-extension-0.4.73.zip' 'manifest-public-key.der' '.incoming/foo'; do
  [[ "$(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$base/$suffix")" == 404 ]]
done
[[ "$(curl -sS --max-time 5 -X POST -o /dev/null -w '%{http_code}' "$base/latest.json")" == 403 ]]
[[ "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json)" == 401 ]]
ok=1
echo WINDOWS_STABLE_HTTP_CONTRACT_VERIFIED_PUBLIC_CLOSED
