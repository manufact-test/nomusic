#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/home/celikom-mirror/.ssh
R=/home/celikom-mirror/github-mirror.git
echo '=== Check private/public key pairs ==='
for name in github-readonly forgejo-write; do
  derived=$(runuser -u celikom-mirror -- ssh-keygen -y -P '' -f "$S/$name" | ssh-keygen -lf - | awk '{print $2}')
  declared=$(ssh-keygen -lf "$S/$name.pub" | awk '{print $2}')
  printf '%s derived=%s declared=%s match=' "$name" "$derived" "$declared"
  [[ "$derived" == "$declared" ]] && echo YES || { echo NO; exit 1; }
done
echo '=== Test exact GitHub source key ==='
GH="ssh -i $S/github-readonly -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/known_hosts -o BatchMode=yes -o ConnectTimeout=10"
runuser -u celikom-mirror -- env GIT_SSH_COMMAND="$GH" git ls-remote git@github.com:manufact-test/nomusic.git refs/heads/main
echo '=== Test exact Forgejo destination key ==='
FG="ssh -i $S/forgejo-write -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$S/forgejo_known_hosts -o BatchMode=yes -o ConnectTimeout=10"
runuser -u celikom-mirror -- env GIT_SSH_COMMAND="$FG" git ls-remote git@127.0.0.1:celadmin/nomusic.git HEAD
echo CELIKOM_MIRROR_BOTH_KEYS_AUTHENTICATED
