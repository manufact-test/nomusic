#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Scheduled Forgejo tick after 20:30 ==='
systemctl show celikom-mirror-sync.timer -p LastTriggerUSec -p NextElapseUSecRealtime
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus -p ExecMainExitTimestamp
journalctl -u celikom-mirror-sync.service --since '2026-11-24 20:29:30 UTC' --no-pager -o short-iso | grep -E 'VERIFIED_REFS=|CELIKOM_MIRROR_SYNC_OK|Permission denied|fatal:|Failed to start' | tail -n 12
runuser -u celikom-mirror -- bash -c '
set -euo pipefail
S=/home/celikom-mirror/.ssh
R=/home/celikom-mirror/github-mirror.git
GH="ssh -i $S/github-readonly -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/known_hosts -o BatchMode=yes"
FG="ssh -i $S/forgejo-write -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/forgejo_known_hosts -o BatchMode=yes"
gh=$(GIT_SSH_COMMAND="$GH" git ls-remote git@github.com:manufact-test/nomusic.git refs/heads/main | awk "{print \$1}")
local=$(git --git-dir="$R" rev-parse refs/heads/main)
fj=$(GIT_SSH_COMMAND="$FG" git --git-dir="$R" ls-remote git@127.0.0.1:celadmin/nomusic.git refs/heads/main | awk "{print \$1}")
printf "GITHUB_MAIN=%s\nLOCAL_MIRROR_MAIN=%s\nFORGEJO_MAIN=%s\n" "$gh" "$local" "$fj"
[[ "$gh" == "$local" && "$local" == "$fj" ]]
'
echo '=== Certbot renewal hook ==='
find /etc/letsencrypt/renewal-hooks/deploy -maxdepth 1 -type f -printf '%f %m %u:%g\n' 2>/dev/null | sort
for f in /etc/letsencrypt/renewal-hooks/deploy/*; do
  [[ -f "$f" ]] || continue
  bash -n "$f"
  sed -n '1,120p' "$f"
done
echo '=== Current CELIKOM Nginx routing and real-IP directives ==='
for f in /etc/nginx/sites-enabled/*celikom* /etc/nginx/conf.d/*celikom*; do
  [[ -f "$f" ]] || continue
  echo "FILE=$f"
  grep -nE 'server_name|set_real_ip_from|real_ip_header|real_ip_recursive|auth_basic|client_max_body_size|limit_req|proxy_set_header|fastcgi_param REMOTE_ADDR|fastcgi_pass|proxy_pass' "$f" || true
done
echo '=== Prepared API/site candidate real-IP directives ==='
for f in /root/celikom-cutover-prepared/*.conf; do
  [[ -f "$f" ]] || continue
  echo "FILE=$(basename "$f")"
  grep -nE 'server_name|set_real_ip_from|real_ip_header|real_ip_recursive|auth_basic|client_max_body_size|limit_req|proxy_set_header|fastcgi_param REMOTE_ADDR|fastcgi_pass|proxy_pass' "$f" || true
done
echo '=== Public API route state ==='
for path in /api/v1/health /api/v1/config /api/v1/auth /api/v1/resolve /admin/login; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "https://api.celikom.com$path")
  printf '%s %s\n' "$path" "$code"
done
echo CELIKOM_SCHEDULED_MIRROR_TLS_HOOK_AND_API_ROUTE_AUDIT_OK
