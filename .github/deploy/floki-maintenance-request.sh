#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Exercise the installed Certbot deploy hook ==='
bash /etc/letsencrypt/renewal-hooks/deploy/celikom-nginx.sh
systemctl is-active nginx
echo '=== Verify HTTPS immediately after hook reload ==='
for spec in   'https://celikom.com/ 401'   'https://celikom.com/admin/ 401'   'https://api.celikom.com/api/v1/health 200'   'https://api.celikom.com/api/v1/config 200'   'https://api.celikom.com/api/v1/auth 404'   'https://api.celikom.com/api/v1/resolve 404'; do
  url=${spec% *}; want=${spec##* }
  got=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "$url")
  printf '%s expected=%s actual=%s\n' "$url" "$want" "$got"
  [[ "$got" == "$want" ]]
done
echo CELIKOM_CERTBOT_DEPLOY_HOOK_RELOAD_PASS
