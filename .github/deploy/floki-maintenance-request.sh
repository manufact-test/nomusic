#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Mirror service contract ==='
systemctl cat celikom-mirror-sync.service | sed -E '/Environment(File)?=/s/=.*/=[REDACTED]/'
echo '=== Sync executable (secrets excluded) ==='
sed -n '1,240p' /usr/local/sbin/celikom-mirror-sync | sed -E 's/(TOKEN|PASSWORD|SECRET|PRIVATE_KEY)=.*/\1=[REDACTED]/I'
echo '=== SSH client configuration ==='
runuser -u celikom-mirror -- ssh -G git@127.0.0.1 2>/dev/null | grep -E '^(hostname|user|port|identityfile|identitiesonly|identityagent|proxycommand|proxyjump) '
echo '=== Mirror account SSH file metadata and public fingerprints ==='
find /home/celikom-mirror/.ssh -maxdepth 1 -type f -printf '%f %m %u:%g %s bytes\n' 2>/dev/null | sort || true
for f in /home/celikom-mirror/.ssh/*.pub; do
  [[ -f "$f" ]] && ssh-keygen -lf "$f" || true
done
echo '=== Forgejo authorized public key fingerprints ==='
for f in /var/lib/forgejo/.ssh/authorized_keys /home/git/.ssh/authorized_keys /var/lib/gitea/.ssh/authorized_keys; do
  if [[ -f "$f" ]]; then
    echo "FILE=$f"
    ssh-keygen -lf "$f" || true
  fi
done
echo '=== Read-only authenticated push endpoint probe ==='
runuser -u celikom-mirror -- env GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes' git ls-remote forgejo HEAD 2>&1 | head -n 8 || true
echo CELIKOM_FORGEJO_SSH_DIAGNOSTIC_OK
