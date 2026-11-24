#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
systemctl start celikom-mirror-sync.service
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus -p ExecMainExitTimestamp
R=/home/celikom-mirror/github-mirror.git
GH=/home/celikom-mirror/.ssh/github-readonly
FG=/home/celikom-mirror/.ssh/forgejo-write
GHCMD="ssh -i $GH -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/home/celikom-mirror/.ssh/known_hosts -o BatchMode=yes"
FGCMD="ssh -i $FG -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/home/celikom-mirror/.ssh/forgejo_known_hosts -o BatchMode=yes"
gh=$(GIT_SSH_COMMAND="$GHCMD" git ls-remote git@github.com:manufact-test/nomusic.git refs/heads/main | awk '{print $1}')
local=$(git --git-dir="$R" rev-parse refs/heads/main)
fj=$(GIT_SSH_COMMAND="$FGCMD" git --git-dir="$R" ls-remote git@127.0.0.1:celadmin/nomusic.git refs/heads/main | awk '{print $1}')
printf 'GITHUB_MAIN=%s\nLOCAL_MIRROR_MAIN=%s\nFORGEJO_MAIN=%s\n' "$gh" "$local" "$fj"
[[ "$gh" == "$local" && "$local" == "$fj" ]]
S=/srv/celikom/app/staging-20261122
for rel in server/src/Admin/AdminPanel.php server/src/Admin/ModerationService.php server/src/Application/UploadService.php server/src/Admin/admin-style.css server/config/app.php .env.example; do
  stage="$S/${rel#server/}"
  [[ -f "$stage" ]] || { echo "STAGE_MISSING $rel"; continue; }
  tmp=$(mktemp)
  git --git-dir="$R" show "refs/heads/main:$rel" > "$tmp"
  diff -u "$tmp" "$stage" > /tmp/celikom-one-diff.txt || true
  plus=$(grep -c '^+' /tmp/celikom-one-diff.txt || true)
  minus=$(grep -c '^-' /tmp/celikom-one-diff.txt || true)
  hunks=$(grep -c '^@@' /tmp/celikom-one-diff.txt || true)
  printf 'SOURCE_DIFF %s stage_added=%s repo_only=%s hunks=%s\n' "$rel" "$((plus>2?plus-2:0))" "$((minus>2?minus-2:0))" "$hunks"
  grep '^@@' /tmp/celikom-one-diff.txt | head -n 8 || true
  rm -f "$tmp"
done
echo '=== Git history for missing migration ==='
git --git-dir="$R" log --all --oneline -- server/migrations/019_bulk_moderation_tombstones.sql | head -n 10 || true
git --git-dir="$R" ls-tree -r --name-only refs/heads/main | grep -E 'bulk_moderation|Mp3Normalizer|Mp3DecodeValidator|mp3-validator' || true
echo CELIKOM_MIRROR_SOURCE_DRIFT_AUDIT_OK
