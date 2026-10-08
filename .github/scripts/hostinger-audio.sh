#!/usr/bin/env bash
set -euo pipefail

[[ "$GITHUB_EVENT_NAME" == 'push' || "$GITHUB_EVENT_NAME" == 'workflow_dispatch' ]] || exit 1
[[ "$GITHUB_REPOSITORY" == 'manufact-test/nomusic' && "$GITHUB_REF" == 'refs/heads/feature/api-range' ]] || exit 1
[[ "$GITHUB_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 1
[[ -n "$HOSTINGER_SSH_KEY" ]] || { echo 'Hostinger deployment key is not configured.' >&2; exit 1; }

node --input-type=module <<'VALIDATE'
import fs from 'node:fs';
const value = JSON.parse(fs.readFileSync('.github/deploy/hostinger-audio-request.json', 'utf8'));
const assert = (condition) => { if (!condition) throw new Error('invalid_private_audio_request'); };
assert(value && typeof value === 'object' && !Array.isArray(value));
const fields = {
  inspect: ['operation'],
  import: ['operation', 'track_id', 'duration_ms', 'confirm_reviewed'],
  enable: ['operation', 'track_id'],
  disable: ['operation'],
};
assert(Object.hasOwn(fields, value.operation));
assert(Object.keys(value).sort().join('|') === fields[value.operation].sort().join('|'));
if (value.operation === 'import' || value.operation === 'enable') assert(typeof value.track_id === 'string' && /^[1-9][0-9]{0,23}$/.test(value.track_id));
if (value.operation === 'import') assert(Number.isSafeInteger(value.duration_ms) && value.duration_ms >= 1000 && value.duration_ms <= 86400000 && value.confirm_reviewed === true);
console.log('Private operation request validated; no credentials or private filenames are used.');
VALIDATE

# Do not allow an old Actions run to re-enable the service after a newer change.
remote_head="$(git ls-remote origin refs/heads/feature/api-range | cut -f1)"
[[ "$remote_head" == "$GITHUB_SHA" ]] || { echo 'A newer branch commit exists; refusing a stale operation.' >&2; exit 1; }

umask 077
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$work/key"
ssh-keygen -y -P '' -f "$work/key" > "$work/public"
[[ "$(ssh-keygen -lf "$work/public" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || { echo 'Unexpected deployment key.' >&2; exit 1; }
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$work/known_hosts"
options=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15)
target='u235811320@92.113.19.189'
site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'
incoming="$site/celikom/incoming/audio-operation-$GITHUB_SHA"
php_bin='/opt/alt/php83/usr/bin/php'

ssh -T -p 65002 "${options[@]}" "$target" "test -d '$site/public_html' && test ! -L '$site/celikom' && umask 077 && mkdir -p '$incoming' && chmod 0700 '$incoming'"
scp -P 65002 "${options[@]}" .github/scripts/hostinger-audio-remote.php .github/deploy/hostinger-audio-request.json "$target:$incoming/"
ssh -T -p 65002 "${options[@]}" "$target" "'$php_bin' '$incoming/hostinger-audio-remote.php' '$incoming/hostinger-audio-request.json'"
ssh -T -p 65002 "${options[@]}" "$target" "rm -f '$incoming/hostinger-audio-remote.php' '$incoming/hostinger-audio-request.json' && rmdir '$incoming'"

node --input-type=module <<'CHECK'
import assert from 'node:assert/strict';
import fs from 'node:fs';
const { operation } = JSON.parse(fs.readFileSync('.github/deploy/hostinger-audio-request.json', 'utf8'));
const response = await fetch('https://darkred-camel-588676.hostingersite.com/api/v1/config', { signal: AbortSignal.timeout(20000), cache: 'no-store' });
assert.equal(response.status, 200);
const result = await response.json();
assert.equal(result.api_version, 1);
assert.equal(result.features.analytics, false);
if (operation === 'enable') assert.equal(result.features.replacements, true);
else assert.equal(result.features.replacements, false);
console.log('Public HTTPS config matches the requested safe feature state.');
CHECK
