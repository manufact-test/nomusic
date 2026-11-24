#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== Recovery inventory (metadata only) ==='
df -h /srv /root
find /root /srv/celikom -xdev -type f \( -name 'celikom-offsite-*.tar.gpg' -o -name '*.age' -o -name '*.bundle' \) -printf '%p %s bytes\n' 2>/dev/null | sort
for path in /root/celikom-cutover-snapshot-YaDz8eHD/intake/api.sql.gz /root/celikom-cutover-snapshot-YaDz8eHD/intake/cms.sql.gz /srv/celikom/migration/refresh-20261124-151155/database/celikom.sql.gz /srv/celikom/migration/sites-20261124/database/cms.sql.gz; do
  test -f "$path" && test ! -L "$path"
  gzip -t "$path"
  sha256sum "$path"
done
for d in /srv/celikom/migration/sites-20261124/android-public /srv/celikom/migration/sites-20261124/android-private /srv/celikom/migration/sites-20261124/api-public /srv/celikom/data/candidate-20261124/audio; do
  test -d "$d"
  printf '%s files=' "$d"
  find "$d" -type f | wc -l
done
echo '=== Encryption availability ==='
for cmd in age gpg tar; do command -v "$cmd" || true; done
echo '=== Scheduled renewal and runner status ==='
systemctl is-enabled certbot.timer
systemctl is-active certbot.timer
systemctl show certbot.timer -p NextElapseUSecRealtime
systemctl is-active celikom-ci-runner.service
systemctl is-active celikom-mirror-sync.timer
systemctl show celikom-mirror-sync.service -p Result -p ExecMainStatus
echo CELIKOM_RECOVERY_INVENTORY_OK
