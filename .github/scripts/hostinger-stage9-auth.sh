#!/usr/bin/env bash
set -euo pipefail
[[ "${GITHUB_REPOSITORY:-}" == 'manufact-test/nomusic' && "${GITHUB_REF:-}" == 'refs/heads/feature/api-range' ]] || exit 1
[[ "${GITHUB_SHA:-}" =~ ^[a-f0-9]{40}$ ]] || exit 1
operation="$(node -p "require('./.github/deploy/hostinger-stage9-auth-request.json').operation")"
if [[ "$operation" == 'prepare' ]]; then
  echo 'Stage 9 customer auth switch prepared; server unchanged.'
  exit 0
fi
[[ "$operation" == 'enable' || "$operation" == 'disable' ]] || exit 1
[[ -n "${HOSTINGER_SSH_KEY:-}" ]] || exit 1
remote_head="$(git ls-remote origin refs/heads/feature/api-range | cut -f1)"
[[ "$remote_head" == "$GITHUB_SHA" ]] || { echo 'Stale Stage 9 switch refused.' >&2; exit 1; }
umask 077
work="$(mktemp -d)"
opts=()
site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'
target='u235811320@92.113.19.189'
incoming="$site/celikom/incoming/stage9-$GITHUB_SHA"
cleanup() {
  if [[ ${#opts[@]} -gt 0 ]]; then
    ssh -T -p 65002 "${opts[@]}" "$target" "rm -f '$incoming/hostinger-stage9-auth-remote.php' '$incoming/hostinger-stage9-auth-request.json' && rmdir '$incoming'" >/dev/null 2>&1 || true
  fi
  rm -rf -- "$work"
}
trap cleanup EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/public"
[[ "$(ssh-keygen -lf "$work/public" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || exit 1
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
opts=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes
      -o "UserKnownHostsFile=$work/known_hosts" -o GlobalKnownHostsFile=/dev/null
      -o ConnectTimeout=15 -o ServerAliveInterval=10 -o ServerAliveCountMax=2)
ssh -T -p 65002 "${opts[@]}" "$target" "test -d '$site/public_html' && test ! -L '$site/celikom' && umask 077 && mkdir -p '$incoming' && chmod 0700 '$incoming'"
scp -P 65002 "${opts[@]}" .github/scripts/hostinger-stage9-auth-remote.php \
  .github/deploy/hostinger-stage9-auth-request.json "$target:$incoming/"
ssh -T -p 65002 "${opts[@]}" "$target" \
  "/opt/alt/php83/usr/bin/php '$incoming/hostinger-stage9-auth-remote.php' '$incoming/hostinger-stage9-auth-request.json'"
echo 'Stage 9 guarded Hostinger customer authorization switch complete.'
