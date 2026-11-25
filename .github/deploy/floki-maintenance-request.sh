#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only media parity and newest SQL staging inventory; no change to public routes.
snapshot=/root/celikom-cutover-snapshot-Cvt6DJjh/intake
for kind in api cms; do
  test -f "$snapshot/$kind.sql.gz" && test ! -L "$snapshot/$kind.sql.gz"
  gzip -t "$snapshot/$kind.sql.gz"
done
printf 'NEWEST_API_SQL_HASH=%s\n' "$(sha256sum "$snapshot/api.sql.gz" | cut -d' ' -f1)"
printf 'NEWEST_CMS_SQL_HASH=%s\n' "$(sha256sum "$snapshot/cms.sql.gz" | cut -d' ' -f1)"
test -z "$(find /etc/nginx/conf.d -maxdepth 1 -name 'celikom-cutover-probe.conf' -print)"
mapfile -t boots < <(find /srv/celikom-site -maxdepth 5 -type f -path '*/app/bootstrap.php')
[[ "${#boots[@]}" == 1 ]]
siteboot="${boots[0]}"
audio=/srv/celikom/data/candidate-20261124/audio
media=$(runuser -u celikom-site -- php -r 'require $argv[1];$m=getenv("CELIKOM_SITE_MEDIA_DIR");if(!is_string($m)||!is_dir($m))exit(2);echo realpath($m);' "$siteboot")
[[ "$media" == /srv/celikom-site/* && -d "$audio" ]]
file_fingerprint(){
  cd "$1"
  find . -type f -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum | sha256sum | awk -v kind="$2" '{print "FILE_FINGERPRINT",kind,$1}'
}
(file_fingerprint "$audio" audio)
(file_fingerprint "$media" cms-media)



echo CELIKOM_TARGET_FINGERPRINT_OK

