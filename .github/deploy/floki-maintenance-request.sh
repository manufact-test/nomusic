#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Independent scheduled Forgejo mirror tick ==='
systemctl show celikom-mirror-sync.timer -p LastTriggerUSec -p NextElapseUSecRealtime
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus -p ExecMainExitTimestamp
journalctl -u celikom-mirror-sync.service --since '2026-11-24 20:14:00 UTC' --no-pager -o short-iso | grep -E 'Started CELIKOM|VERIFIED_REFS=|CELIKOM_MIRROR_SYNC_OK|Permission denied|fatal:|Failed to start' | tail -n 30
runuser -u celikom-mirror -- bash -c '
set -euo pipefail
S=/home/celikom-mirror/.ssh
R=/home/celikom-mirror/github-mirror.git
GH="ssh -i $S/github-readonly -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/known_hosts -o BatchMode=yes"
FG="ssh -i $S/forgejo-write -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/forgejo_known_hosts -o BatchMode=yes"
gh=$(GIT_SSH_COMMAND="$GH" git ls-remote git@github.com:manufact-test/nomusic.git refs/heads/main | awk "{print \$1}")
local=$(git --git-dir="$R" rev-parse refs/heads/main)
fj=$(GIT_SSH_COMMAND="$FG" git --git-dir="$R" ls-remote git@127.0.0.1:celadmin/nomusic.git refs/heads/main | awk "{print \$1}")
printf "GITHUB_MAIN=%s\nLOCAL_MIRROR_MAIN=%s\nFORGEJO_MAIN=%s\n" "$gh" "$local" "$fj"
[[ "$gh" == "$local" && "$local" == "$fj" ]]
'
echo CELIKOM_SCHEDULED_MIRROR_MAIN_EQUAL_OK
