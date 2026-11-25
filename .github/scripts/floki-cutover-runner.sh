#!/bin/bash
set -Eeuo pipefail
set +x
umask 077
export PATH=/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
[[ "$GITHUB_REPOSITORY" == manufact-test/nomusic && "$GITHUB_REF" == refs/heads/main ]]
test -n "$HOSTINGER_SSH_KEY" && test -n "$FLOKI_DEPLOY_CONNECTION" && test -n "$GH_TOKEN"
for script in floki-cutover-source-freeze.sh floki-cutover-target-activate.sh floki-final-db-dump.sh floki-final-db-intake.sh floki-final-db-verify.sh floki-final-db-cleanup.sh; do
  bash -n ".github/scripts/$script"
done
[[ "$(gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main" --jq .object.sha)" == "$GITHUB_SHA" ]]
echo CELIKOM_FINAL_CUTOVER_PINNED_MAIN_AND_SYNTAX_OK
tmp=$(mktemp -d)
printf '%s\n' "$HOSTINGER_SSH_KEY" | tr -d '\r' > "$tmp/source-key"
unset HOSTINGER_SSH_KEY
printf '%s\n' "$FLOKI_DEPLOY_CONNECTION" | tr -d '\r' > "$tmp/bundle"
unset FLOKI_DEPLOY_CONNECTION
head -n 1 "$tmp/bundle" > "$tmp/target-known"
tail -n +2 "$tmp/bundle" > "$tmp/target-key"
rm -f "$tmp/bundle"
ssh-keygen -y -P '' -f "$tmp/source-key" > "$tmp/source.pub"
[[ "$(ssh-keygen -lf "$tmp/source.pub" | awk '{print $2}')" == 'SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk' ]]
ssh-keygen -y -P '' -f "$tmp/target-key" >/dev/null
grep -Eq '^95\.133\.160\.111 ssh-ed25519 [A-Za-z0-9+/=]+$' "$tmp/target-known"
printf '%s\n' '[92.113.19.189]:65002 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAf8M2EVwq0oJI8I9KZ0NFE8P8yDOvDATEhkQti/Kk/0' > "$tmp/source-known"
source_ssh=(-T -p 65002 -i "$tmp/source-key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$tmp/source-known" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=20 -o ClearAllForwardings=yes)
target_ssh=(-T -i "$tmp/target-key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$tmp/target-known" -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=20 -o ClearAllForwardings=yes)
frozen=0
intake=0
switched=0
cleanup(){
  rc=$?
  trap - EXIT
  if [[ "$intake" == 1 ]]; then
    ssh "${target_ssh[@]}" celikom-deploy@95.133.160.111 maintenance < .github/scripts/floki-final-db-cleanup.sh || rc=1
  fi
  if [[ "$switched" != 1 && "$frozen" == 1 ]]; then
    ssh "${source_ssh[@]}" u235811320@92.113.19.189 'bash -s -- rollback' < .github/scripts/floki-cutover-source-freeze.sh || rc=1
  fi
  rm -rf -- "$tmp"
  exit "$rc"
}
trap cleanup EXIT
# Safe verified owner-only source freeze for the exact two sites.
ssh "${source_ssh[@]}" u235811320@92.113.19.189 'bash -s -- freeze' < .github/scripts/floki-cutover-source-freeze.sh
frozen=1
ssh "${source_ssh[@]}" u235811320@92.113.19.189 'bash -s -- status' < .github/scripts/floki-cutover-source-freeze.sh
# Unmatched routes return 404 without Basic Auth before freeze. Require 403
# specifically from the newly inserted mod_rewrite [F] rule on both old sites.
for url in \
  https://darkred-camel-588676.hostingersite.com/__celikom_freeze_probe_20261125 \
  https://lemonchiffon-narwhal-791953.hostingersite.com/__celikom_freeze_probe_20261125; do
  code=$(curl --silent --show-error --location --max-redirs 3 --max-time 20 -X POST -o /dev/null -w '%{http_code}' "$url")
  [[ "$code" == 403 ]] || { echo "SOURCE_WRITE_FREEZE_NOT_EFFECTIVE $code"; exit 1; }
done
[[ "$(curl --silent --show-error --max-time 15 -o /dev/null -w '%{http_code}' https://darkred-camel-588676.hostingersite.com/api/v1/health)" == 200 ]]
sleep 4
echo CELIKOM_SOURCE_WRITE_METHODS_FROZEN
# Rehash content under freeze, not a previous-day count or timestamp.
ssh "${source_ssh[@]}" u235811320@92.113.19.189 'bash -s' <<'REMOTE_MEDIA'
set -Eeuo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
audio=/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/shared/audio
media=/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com/celikom-private/media
test -d "$audio" && test -d "$media"
fingerprint(){ (cd "$1" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1); }
[[ "$(fingerprint "$audio")" == 9240eeba545d433d2fec25690c8d740de729d614db4c28f40ca91bea6b6c24ed ]]
[[ "$(fingerprint "$media")" == 567dddbeb64aa8707bf9d54f9569313685652d058f6731cee06c3e2acecd9ed6 ]]
echo FINAL_SOURCE_AUDIO_CMS_MEDIA_BYTES_MATCH_FLOKI
REMOTE_MEDIA
# Transfer new SQL after freeze; keep both SSH keys only on the ephemeral runner.
for kind in api cms; do
  ssh "${source_ssh[@]}" u235811320@92.113.19.189 "bash -s -- $kind" \
    < .github/scripts/floki-final-db-dump.sh > "$tmp/$kind.sql.gz"
  gzip -t "$tmp/$kind.sql.gz"
  test "$(stat -c %s "$tmp/$kind.sql.gz")" -gt 100
done
ssh "${target_ssh[@]}" celikom-deploy@95.133.160.111 maintenance < .github/scripts/floki-final-db-intake.sh
intake=1
for kind in api cms; do
  expected=$(sha256sum "$tmp/$kind.sql.gz" | cut -d' ' -f1)
  actual=$(ssh "${target_ssh[@]}" celikom-deploy@95.133.160.111 "receive-cutover-$kind" < "$tmp/$kind.sql.gz")
  [[ "$actual" == "$expected" ]] || { echo "FINAL_SQL_TRANSFER_HASH_MISMATCH $kind"; exit 1; }
  echo "FINAL_SQL_SOURCE_TARGET_SHA_MATCH $kind $expected"
done
ssh "${target_ssh[@]}" celikom-deploy@95.133.160.111 maintenance < .github/scripts/floki-final-db-verify.sh
echo FINAL_FROZEN_SQL_INDEPENDENT_RESTORE_OK
# Do not activate unless the original source freeze still exists.
ssh "${source_ssh[@]}" u235811320@92.113.19.189 'bash -s -- status' < .github/scripts/floki-cutover-source-freeze.sh
ssh "${target_ssh[@]}" celikom-deploy@95.133.160.111 maintenance < .github/scripts/floki-cutover-target-activate.sh
switched=1
echo CELIKOM_FINAL_NEW_PUBLIC_API_ACCEPTED_OLD_WRITES_FROZEN
