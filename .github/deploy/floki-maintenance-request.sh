#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Run scheduled mirror job once ==='
systemctl start celikom-mirror-sync.service
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus -p ExecMainExitTimestamp
journalctl -u celikom-mirror-sync.service -n 35 --no-pager -o cat | grep -E 'FETCH GITHUB|PUSH FORGEJO|VERIFIED_REFS=|CELIKOM_MIRROR_SYNC_OK|Permission denied|fatal:|error:|Failed to start' || true
echo '=== Independent mirror refs comparison ==='
runuser -u celikom-mirror -- bash -c '
set -euo pipefail
R=/home/celikom-mirror/github-mirror.git
S=/home/celikom-mirror/.ssh
tmp=$(mktemp -d)
trap "rm -rf \"$tmp\"" EXIT
git --git-dir="$R" for-each-ref --format="%(objectname) %(refname)" refs/heads refs/tags | LC_ALL=C sort > "$tmp/local"
FG="ssh -i $S/forgejo-write -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/forgejo_known_hosts -o BatchMode=yes"
GIT_SSH_COMMAND="$FG" git --git-dir="$R" ls-remote --heads --tags forgejo | awk "\$2 !~ /\\^\\{\\}$/ {print \$1 \" \" \$2}" | LC_ALL=C sort > "$tmp/remote"
cmp "$tmp/local" "$tmp/remote"
echo "MIRROR_EXACT_REFS=$(wc -l < "$tmp/local")"
'
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus
echo CELIKOM_MIRROR_REPAIR_RECHECK_OK
