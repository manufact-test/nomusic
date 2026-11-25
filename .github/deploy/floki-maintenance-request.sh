#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
root=/srv/celikom/migration
archive="$root/backups/celikom-offsite-20261122.tar.gpg"
key="$root/secrets/celikom-offsite-20261122.key"
[[ -f "$archive" && ! -L "$archive" && -f "$key" && ! -L "$key" ]]
[[ "$(stat -c '%u:%a:%s' "$key")" =~ ^0:(400|600):[1-9][0-9]*$ ]]
[[ "$(stat -c %s "$archive")" == 9733284276 ]]
printf '%s  %s\n' 9d94a07d3306acd8874a7d3ad959234427d67a0d1b9c402526abb492e3acff15 "$archive" | sha256sum -c --status
echo EXISTING_OWNER_OFFSITE_BASE_CIPHERTEXT_AND_RECOVERY_KEY_PRESENT
df -B1 --output=avail "$root" | tail -1 | awk '{print "MIGRATION_DISK_AVAILABLE_BYTES",$1}'
for command in gpg tar gzip python3 docker mariadb-dump mysqldump sha256sum; do
 if command -v "$command" >/dev/null; then echo "RECOVERY_TOOL_READY $command"; else echo "RECOVERY_TOOL_MISSING $command"; fi
done
docker images --format 'RESTORE_IMAGE {{.Repository}}:{{.Tag}}' | grep -E 'mariadb|mysql' | head -n 10 || true
find /srv/celikom-releases/private -maxdepth 4 -type f \( -iname '*.exe' -o -iname '*.apk' -o -iname '*.zip' \) -printf 'PRIVATE_RELEASE_FILE %P %s\n' | head -n 35
for cfg in /srv/celikom/app/staging-20261122/.env /srv/celikom-site/celikom-private/staging-config.php /etc/nginx/sites-available/celikom-api-https /etc/nginx/sites-available/celikom-site-https; do
 test -f "$cfg" && test ! -L "$cfg"
 echo "LIVE_BACKUP_INPUT_EXISTS $(basename "$cfg")"
done
echo CELIKOM_FINAL_OFFSITE_INCREMENTAL_PREPARED_INPUTS_OK
