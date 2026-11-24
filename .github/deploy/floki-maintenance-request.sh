#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Mirror sync last failure ==='
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus -p ExecMainExitTimestamp
systemctl show celikom-mirror-sync.timer -p LastTriggerUSec -p NextElapseUSecRealtime
journalctl -u celikom-mirror-sync.service --since '90 minutes ago' --no-pager -o cat | python3 -c 'import sys,re
for s in sys.stdin:
    if re.search(r"fatal:|error:|failed|denied|rejected|VERIFIED_REFS=|CELIKOM_MIRROR_SYNC_OK|exit-code|timed out|could not|unable to|lock",s,re.I):
        s=re.sub(r"https?://[^\s]+","[URL]",s)
        s=re.sub(r"(?i)(authorization:|bearer |token=|password=).*",r"\1[REDACTED]",s)
        print(s[:500].rstrip())' | tail -n 45
echo '=== Mirror local state ==='
runuser -u celikom-mirror -- git --git-dir=/home/celikom-mirror/github-mirror.git rev-parse refs/heads/main
runuser -u celikom-mirror -- git --git-dir=/home/celikom-mirror/github-mirror.git for-each-ref --format='%(refname)' | wc -l
echo '=== Verify existing offsite ciphertext ==='
archive=/srv/celikom/migration/backups/celikom-offsite-20261122.tar.gpg
printf '%s  %s\n' 9d94a07d3306acd8874a7d3ad959234427d67a0d1b9c402526abb492e3acff15 "$archive" | sha256sum -c -
echo CELIKOM_MIRROR_DIAGNOSTIC_AND_BACKUP_HASH_OK
