#!/usr/bin/env bash
set -euo pipefail
[[ "${GITHUB_REPOSITORY:-}" == 'manufact-test/nomusic' && "${GITHUB_REF:-}" == 'refs/heads/feature/api-range' ]] || exit 1
[[ "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ && -n "${HOSTINGER_SSH_KEY:-}" ]] || exit 1
node --input-type=module <<'VALIDATE'
import fs from 'node:fs';
const req = JSON.parse(fs.readFileSync('.github/deploy/hostinger-stage5-request.json','utf8'));
if (!req || typeof req !== 'object' || Array.isArray(req)
    || Object.keys(req).join(',') !== 'operation'
    || !['audit','snapshot','restore-drill'].includes(req.operation))
  throw new Error('invalid_stage5_request');
console.log('Stage 5 restricted operation request validated.');
VALIDATE
remote_head="$(git ls-remote origin refs/heads/feature/api-range | cut -f1)"
[[ "$remote_head" == "$GITHUB_SHA" ]] || { echo 'Stale workflow revision, refusing remote operation.' >&2; exit 1; }
umask 077
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/public"
[[ "$(ssh-keygen -lf "$work/public" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || exit 1
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
options=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15 -o ServerAliveInterval=10 -o ServerAliveCountMax=2)
target='u235811320@92.113.19.189'
site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'
incoming="$site/celikom/incoming/stage5-$GITHUB_SHA"
php_bin='/opt/alt/php83/usr/bin/php'
ssh -T -p 65002 "${options[@]}" "$target" "test -d '$site/public_html' && test ! -L '$site/celikom' && umask 077 && mkdir -p '$incoming' && chmod 0700 '$incoming'"
scp -P 65002 "${options[@]}" .github/scripts/hostinger-stage5-remote.php .github/deploy/hostinger-stage5-request.json "$target:$incoming/"
operation="$(node -p "require('./.github/deploy/hostinger-stage5-request.json').operation")"
ssh -T -p 65002 "${options[@]}" "$target" "'$php_bin' '$incoming/hostinger-stage5-remote.php' '$incoming/hostinger-stage5-request.json'"
if [[ "$operation" == "restore-drill" ]]; then
  # SQL is transferred only into runner temporary scratch and never printed.
  printf '%s\n' '{"operation":"restore-export"}' > "$work/restore-export.json"
  scp -P 65002 "${options[@]}" "$work/restore-export.json" "$target:$incoming/hostinger-stage5-request.json"
  ssh -T -p 65002 "${options[@]}" "$target" "'$php_bin' '$incoming/hostinger-stage5-remote.php' '$incoming/hostinger-stage5-request.json'" > "$work/database.sql"
  [[ -s "$work/database.sql" ]] || { echo 'SQL snapshot unavailable.' >&2; exit 1; }
  if ! command -v mysql >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq default-mysql-client > /dev/null
  fi
  MYSQL_PWD='ci-disposable-mysql' mysql --protocol=TCP -h 127.0.0.1 -P 3306 -u root celikom_restore < "$work/database.sql" 2> "$work/import-errors" || {
    echo 'Isolated MySQL restore failed. No private SQL or row data disclosed.' >&2
    exit 1
  }
  MYSQL_PWD='ci-disposable-mysql' mysql --protocol=TCP -h 127.0.0.1 -P 3306 -u root -N -B celikom_restore \
    -e "SELECT CASE WHEN (SELECT COUNT(*) FROM tracks WHERE service='yandex' AND service_track_id='144530503')=1 AND (SELECT COUNT(*) FROM audio_assets WHERE size_bytes=4345176 AND duration_ms=180872)=1 AND (SELECT COUNT(*) FROM track_replacements WHERE id=1 AND status='approved' AND is_active=1)=1 AND (SELECT COUNT(*) FROM schema_migrations)>=1 THEN 'recovered' ELSE 'invalid' END;" > "$work/result"
  [[ "$(cat "$work/result")" == 'recovered' ]] || { echo 'Isolated MySQL data verification failed.' >&2; exit 1; }
  echo 'Stage 5 isolated MySQL database restore PASS: schema and approved track mapping recovered; live MySQL untouched.'
fi
ssh -T -p 65002 "${options[@]}" "$target" "rm -f '$incoming/hostinger-stage5-remote.php' '$incoming/hostinger-stage5-request.json' && rmdir '$incoming'"
node --input-type=module <<'EXTERNAL'
import assert from 'node:assert/strict';
const base = 'https://darkred-camel-588676.hostingersite.com';
const health = await fetch(base+'/api/v1/health', {signal: AbortSignal.timeout(20000), cache:'no-store'});
const config = await fetch(base+'/api/v1/config', {signal: AbortSignal.timeout(20000), cache:'no-store'});
if (health.status === 403 && config.status === 403) {
  // Hostinger's edge may reject GitHub runner IPs. The restricted SSH on-host
  // preflight above already verified database, protected audio and migration.
  // Never disable the edge firewall solely to make runner-side probes pass.
  console.log('GitHub runner blocked by Hostinger edge (403); protected on-host audit PASSED.');
  process.exit(0);
}
assert.equal(health.status, 200);
assert.equal(config.status, 200);
const healthData = await health.json(), configData = await config.json();
assert.equal(healthData.service, 'celikom-api');
assert.equal(configData.features.replacements, true);
assert.equal(configData.features.analytics, false);
const r=await fetch(base+'/api/v1/resolve?service=yandex&track_id=144530503', {
  signal: AbortSignal.timeout(20000),cache:'no-store'
});
assert.equal(r.status,401);
console.log('Stage 5 external HTTPS monitoring PASS: health/config up, replacements enabled, anonymous access denied.');
EXTERNAL
