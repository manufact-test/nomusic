#!/usr/bin/env bash
set -euo pipefail
[[ "${GITHUB_REPOSITORY:-}" == 'manufact-test/nomusic' && "${GITHUB_REF:-}" == 'refs/heads/feature/api-range' ]] || exit 1
[[ "${GITHUB_SHA:-}" =~ ^[a-f0-9]{40}$ && -n "${HOSTINGER_SSH_KEY:-}" ]] || exit 1
umask 077
scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$scratch/key"
ssh-keygen -y -P '' -f "$scratch/key" > "$scratch/public"
[[ "$(ssh-keygen -lf "$scratch/public" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || exit 1
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$scratch/known_hosts"
ssh_opts=(-i "$scratch/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$scratch/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15)
target='u235811320@92.113.19.189'
remote='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/incoming'
remote_file="$remote/stage7-owner-$GITHUB_SHA.php"
openssl rand -hex 48 > "$scratch/token"
mkdir -p dist/stage7-owner-access
openssl pkeyutl -encrypt -pubin -inkey .github/keys/stage7-owner-transport.pub.pem \
  -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 \
  -in "$scratch/token" -out dist/stage7-owner-access/owner-token.encrypted
scp -P 65002 "${ssh_opts[@]}" .github/scripts/hostinger-stage7-owner-remote.php "$target:$remote_file"
cleanup_remote() { ssh -T -p 65002 "${ssh_opts[@]}" "$target" "rm -f '$remote_file'" || true; }
trap 'cleanup_remote; rm -rf -- "$scratch"' EXIT
ssh -T -p 65002 "${ssh_opts[@]}" "$target" "/opt/alt/php83/usr/bin/php '$remote_file'" < "$scratch/token"
node --input-type=module <<'VERIFY'
import assert from 'node:assert/strict';
const origin = 'https://darkred-camel-588676.hostingersite.com';
const health = await fetch(origin+'/api/v1/health',{cache:'no-store',signal:AbortSignal.timeout(20000)});
assert.equal(health.status,200);
const conf = await (await fetch(origin+'/api/v1/config',{cache:'no-store',signal:AbortSignal.timeout(20000)})).json();
assert.equal(conf.upload_enabled,false,'public uploads must remain disabled');
const anonymous = await fetch(origin+'/api/v1/uploads',{method:'POST',signal:AbortSignal.timeout(20000)});
assert.equal(anonymous.status,401,'owner gate enabled, but anonymous uploads forbidden');
console.log('Private owner-only upload gate enabled, public endpoint protections verified.');
VERIFY
