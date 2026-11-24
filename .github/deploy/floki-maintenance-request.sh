#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Windows signed feed local cryptographic recheck ==='
PIN=$(base64 -w0 /root/celikom-secrets/windows-stable-public.der)
export CELIKOM_STABLE_ORIGIN=https://celikom.com
export CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64="$PIN"
node /root/celikom-release-tools/windows-stable-release-verify.mjs /root/celikom-release-import/windows-02455 0.24.55 2
node /root/celikom-release-tools/windows-stable-existing-latest.mjs /srv/celikom-releases/windows/stable/current/manifest.json /srv/celikom-releases/windows/stable/current/manifest.json.sig
echo '=== Web/API config and public access gates ==='
nginx -t
for spec in   'https://celikom.com/ 401'   'https://celikom.com/admin/ 401'   'https://celikom.com/CELIKOM/Windows/Updates/stable/latest.json 401'   'https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.55.exe 401'   'https://celikom.com/downloads/extension/celikom-extension-0.4.73.zip 401'   'https://api.celikom.com/api/v1/health 200'; do
  url=${spec% *}; want=${spec##* }
  got=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "$url")
  printf '%s expected=%s actual=%s\n' "$url" "$want" "$got"
  [[ "$got" == "$want" ]]
done
echo '=== Certificate renewal dry run ==='
certbot renew --dry-run --cert-name celikom.com
echo CELIKOM_TLS_AND_SIGNED_FEED_LOCAL_RECHECK_OK
