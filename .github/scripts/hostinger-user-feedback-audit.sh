#!/usr/bin/env bash
set -euo pipefail
[[ "${GITHUB_SHA:-}" =~ ^[a-f0-9]{40}$ ]] || exit 1
[[ -n "${HOSTINGER_SSH_KEY:-}" ]] || exit 1
umask 077
work=$(mktemp -d)
target=u235811320@92.113.19.189
remote="/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/incoming/feedback-audit-${GITHUB_RUN_ID}.php"
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/public"
[[ "$(ssh-keygen -lf "$work/public" -E sha256 | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || exit 1
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
opts=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15)
trap 'ssh -p 65002 "${opts[@]}" "$target" "rm -f '\''$remote'\''" || true; rm -rf "$work"' EXIT
scp -P 65002 "${opts[@]}" .github/scripts/hostinger-user-feedback-audit.php "$target:$remote"
ssh -p 65002 "${opts[@]}" "$target" "/opt/alt/php83/usr/bin/php '$remote' '0.4.42-$GITHUB_SHA'"
