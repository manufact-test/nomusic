#!/usr/bin/env bash
set -euo pipefail
[[ "${GITHUB_SHA:-}" =~ ^[a-f0-9]{40}$ ]] || exit 1
[[ -n "${HOSTINGER_SSH_KEY:-}" && -n "${HOSTINGER_DB_PASSWORD:-}" ]] || { echo 'Required Hostinger Actions secrets are missing.' >&2; exit 1; }
version="$(node -p "require('./package.json').version")"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1
release_id="$version-$GITHUB_SHA"
site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'
incoming="$site/celikom/incoming/$release_id"
umask 077
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/public"
[[ "$(ssh-keygen -lf "$work/public" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || { echo 'Unexpected deployment key.' >&2; exit 1; }
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
options=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15 -o ServerAliveInterval=10 -o ServerAliveCountMax=2)
target='u235811320@92.113.19.189'
ssh -T -p 65002 "${options[@]}" "$target" "test -d '$site/public_html' && test ! -L '$site/celikom' && umask 077 && mkdir -p '$incoming'"
cp "dist/celikom-server-$version.zip" "$work/package.zip"
printf '%s  package.zip\n' "$(sha256sum "$work/package.zip" | awk '{print $1}')" > "$work/package.zip.sha256"
scp -P 65002 "${options[@]}" "$work/package.zip" "$work/package.zip.sha256" .github/scripts/hostinger-activate.sh "$target:$incoming/"
node -e 'require("fs").writeFileSync(process.argv[1],JSON.stringify({db_name:"u235811320_celikom",db_user:"u235811320_celikom",db_password:process.env.HOSTINGER_DB_PASSWORD}))' "$work/database.json"
ssh -T -p 65002 "${options[@]}" "$target" "bash '$incoming/hostinger-activate.sh' '$release_id'" < "$work/database.json"
# Check the same API from outside the hosting network; no bearer tokens in logs.
node --input-type=module <<'JS_CHECK'
import assert from 'node:assert/strict';
const base='https://darkred-camel-588676.hostingersite.com';
const health=await fetch(base+'/api/v1/health',{signal:AbortSignal.timeout(20000),headers:{Origin:'https://music.yandex.ru'}});
const config=await fetch(base+'/api/v1/config',{signal:AbortSignal.timeout(20000)});
if (health.status===403 && config.status===403) {
  // Hostinger edge firewall may block GitHub Actions cloud IPs. On-host
  // public HTTPS health/config + MySQL runtime were verified by activate.sh.
  // Do not weaken or disable Hostinger's firewall to make CI green.
  console.log('External GitHub runner blocked by Hostinger edge (403); prior on-host HTTPS and DB checks passed.');
  process.exit(0);
}
assert.equal(health.status,200); assert.equal(health.headers.get('access-control-allow-origin'),'https://music.yandex.ru');
const data=await health.json(); assert.equal(data.service,'celikom-api');
assert.equal(config.status,200);
const unauthorized=await fetch(base+'/api/v1/resolve?service=yandex&track_id=1944599',{signal:AbortSignal.timeout(20000)}); assert.equal(unauthorized.status,401);
console.log('External HTTPS health/config, Yandex CORS and unauthorized-access checks passed.');
JS_CHECK
