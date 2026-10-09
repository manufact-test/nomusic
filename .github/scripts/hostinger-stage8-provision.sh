#!/usr/bin/env bash
set -euo pipefail
[[ "${GITHUB_REPOSITORY:-}" == "manufact-test/nomusic" && "${GITHUB_REF:-}" == "refs/heads/feature/api-range" ]] || exit 1
[[ "${GITHUB_SHA:-}" =~ ^[a-f0-9]{40}$ ]] || exit 1
operation="$(node -p "require('./.github/deploy/hostinger-stage8-request.json').operation")"
if [[ "$operation" == "prepare" ]]; then
  echo "Stage 8 admin bootstrap prepared: no private changes."
  exit 0
fi
[[ "$operation" == "provision" && -n "${HOSTINGER_SSH_KEY:-}" ]] || exit 1
remote_head="$(git ls-remote origin refs/heads/feature/api-range | cut -f1)"
[[ "$remote_head" == "$GITHUB_SHA" ]] || { echo "Stale private owner bootstrap refused." >&2; exit 1; }
umask 077
scratch="$(mktemp -d)"
opts=()
target='u235811320@92.113.19.189'
site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'
incoming="$site/celikom/incoming"
remote="$incoming/stage8-provision-${GITHUB_SHA}.php"
cleanup() {
  if [[ ${#opts[@]} -gt 0 ]]; then
    ssh -T -p 65002 "${opts[@]}" "$target" "rm -f '$remote'" >/dev/null 2>&1 || true
  fi
  rm -rf -- "$scratch"
}
trap cleanup EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$scratch/key"
ssh-keygen -y -P '' -f "$scratch/key" > "$scratch/public"
[[ "$(ssh-keygen -lf "$scratch/public" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || exit 1
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$scratch/known_hosts"
opts=(-i "$scratch/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes
      -o "UserKnownHostsFile=$scratch/known_hosts" -o GlobalKnownHostsFile=/dev/null
      -o ConnectTimeout=15)
openssl rand -hex 32 > "$scratch/password"
ssh -T -p 65002 "${opts[@]}" "$target" "test -d '$incoming' && test ! -L '$site/celikom' && test -L '$site/celikom/current'"
scp -P 65002 "${opts[@]}" .github/scripts/hostinger-stage8-provision-remote.php "$target:$remote"
ssh -T -p 65002 "${opts[@]}" "$target" "/opt/alt/php83/usr/bin/php '$remote'" < "$scratch/password"
# Verify the private server's HTTPS routing, without using or printing credentials.
status="$(ssh -T -p 65002 "${opts[@]}" "$target" "curl --silent --show-error --max-time 20 -o /dev/null -w '%{http_code}' 'https://darkred-camel-588676.hostingersite.com/admin/login'")"
[[ "$status" == '200' ]] || { echo "Private admin HTTPS login unavailable." >&2; exit 1; }
denied="$(ssh -T -p 65002 "${opts[@]}" "$target" "curl --silent --show-error --max-time 20 -o /dev/null -w '%{http_code}' 'https://darkred-camel-588676.hostingersite.com/admin/audio/1'")"
[[ "$denied" == '403' ]] || { echo "Unauthenticated audio protection not confirmed." >&2; exit 1; }
mkdir -p dist/stage8-admin-access
{ printf '%s\n' 'CELIKOM private admin' 'URL: https://darkred-camel-588676.hostingersite.com/admin/login' 'Login: owner'
  printf 'Password: '; cat "$scratch/password"; } > dist/stage8-admin-access/owner-credentials.txt
chmod 0600 dist/stage8-admin-access/owner-credentials.txt
echo "Stage 8 private admin HTTPS login 200 and anonymous audio 403 verified; one-day private GitHub artifact created."
