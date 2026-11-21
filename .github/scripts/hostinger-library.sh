#!/usr/bin/env bash
set -euo pipefail

[[ "$GITHUB_EVENT_NAME" == 'push' || "$GITHUB_EVENT_NAME" == 'workflow_dispatch' ]] || exit 1
[[ "$GITHUB_REPOSITORY" == 'manufact-test/nomusic' && "$GITHUB_REF" == 'refs/heads/feature/api-range' ]] || exit 1
[[ "$GITHUB_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 1

node .github/scripts/hostinger-library-contract.mjs
operation="$(node --input-type=module -e "import { readLibraryRequest } from './.github/scripts/hostinger-library-contract.mjs'; console.log(readLibraryRequest('.github/deploy/hostinger-library-request.json').operation)")"
if [[ "$operation" == 'validate' ]]; then
  echo 'Stage 6 library: validation-only request; no SSH or live database connection.'
  exit 0
fi
[[ -n "${HOSTINGER_SSH_KEY:-}" ]] || { echo 'Hostinger identity not configured.' >&2; exit 1; }
remote_head="$(git ls-remote https://github.com/manufact-test/nomusic.git refs/heads/feature/api-range | cut -f1)"
[[ "$remote_head" == "$GITHUB_SHA" ]] || { echo 'Stale library operation refused.' >&2; exit 1; }

umask 077
scratch="$(mktemp -d)"
remote_created=0
site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'
incoming="$site/celikom/incoming/library-operation-$GITHUB_SHA"
target='u235811320@92.113.19.189'
port=65002
php_bin='/opt/alt/php83/usr/bin/php'
ssh_opts=()
cleanup() {
  if [[ "$remote_created" == 1 ]]; then
    ssh -T -p "$port" "${ssh_opts[@]}" "$target" \
      "rm -f '$incoming/hostinger-library-remote.php' '$incoming/hostinger-library-request.json' '$incoming/LibraryManagementService.php'; rmdir '$incoming'" \
      >/dev/null 2>&1 || true
  fi
  rm -rf -- "$scratch"
}
trap cleanup EXIT

printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$scratch/key"
ssh-keygen -y -P '' -f "$scratch/key" > "$scratch/public"
[[ "$(ssh-keygen -lf "$scratch/public" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]] || {
  echo 'Unexpected deployment SSH identity.' >&2; exit 1;
}
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$scratch/known_hosts"
ssh_opts=(-i "$scratch/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes
  -o "UserKnownHostsFile=$scratch/known_hosts" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=15)

ssh -T -p "$port" "${ssh_opts[@]}" "$target" \
  "test -d '$site/public_html' && test ! -L '$site/celikom' && umask 077 && mkdir -p '$incoming' && chmod 0700 '$incoming'"
remote_created=1
scp -P "$port" "${ssh_opts[@]}" .github/scripts/hostinger-library-remote.php \
  .github/deploy/hostinger-library-request.json "$target:$incoming/"
scp -P "$port" "${ssh_opts[@]}" server/src/Application/LibraryManagementService.php \
  "$target:$incoming/LibraryManagementService.php"
ssh -T -p "$port" "${ssh_opts[@]}" "$target" \
  "CELIKOM_LIBRARY_COMMIT='$GITHUB_SHA' '$php_bin' '$incoming/hostinger-library-remote.php' '$incoming/hostinger-library-request.json'"

# Verify non-secret config invariants; never print signed audio, token or credentials.
node --input-type=module <<'VERIFY'
import assert from "node:assert/strict";
const response = await fetch("https://darkred-camel-588676.hostingersite.com/api/v1/config", {
  signal: AbortSignal.timeout(20000), cache: "no-store"
});
assert.equal(response.status, 200);
const state = await response.json();
assert.equal(state.api_version, 1);
assert.equal(state.features.replacements, true);
assert.equal(state.features.analytics, false);
console.log("Stage 6 public API config unchanged; replacements on, analytics off.");
VERIFY
