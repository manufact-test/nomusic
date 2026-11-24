#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
state=/root/celikom-cutover-intake
for kind in api cms; do
  test -f "$state/$kind.sql.gz" && test ! -L "$state/$kind.sql.gz"
  gzip -t "$state/$kind.sql.gz"
done
# Prove restore without altering the active candidate databases.
container="celikom-cutover-restore-$(date +%s)"
db="celikom_cms_cutover_verify_$(date +%s)"
cleanup(){
  docker rm -f "$container" >/dev/null 2>&1 || true
  mysql --protocol=socket -uroot -e "DROP DATABASE IF EXISTS $db" >/dev/null 2>&1 || true
}
trap cleanup EXIT
docker run --pull=never --network none --name "$container" -e MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1 -d mariadb:11.8.9-noble --innodb-buffer-pool-size=64M --max-allowed-packet=64M --max-connections=8 --performance-schema=OFF >/dev/null
ready=0
for i in $(seq 1 90); do
  if docker logs "$container" 2>&1 | grep -F 'MariaDB init process done. Ready for start up.' >/dev/null && docker exec "$container" mariadb -uroot -Nse 'SELECT 1' >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
[[ "$ready" == 1 ]]
docker exec "$container" mariadb -uroot -e 'CREATE DATABASE celikom_restore CHARACTER SET utf8mb4'
gzip -dc "$state/api.sql.gz" | docker exec -i "$container" mariadb --max-allowed-packet=64M -uroot celikom_restore
docker exec "$container" mariadb -uroot -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='celikom_restore' AND table_type='BASE TABLE'" | grep -x 44
docker exec "$container" mariadb -uroot celikom_restore -Nse 'SELECT "tracks",COUNT(*) FROM tracks UNION ALL SELECT "audio_assets",COUNT(*) FROM audio_assets UNION ALL SELECT "replacements",COUNT(*) FROM track_replacements UNION ALL SELECT "users",COUNT(*) FROM users UNION ALL SELECT "sessions",COUNT(*) FROM user_sessions'
mysql --protocol=socket -uroot -e "CREATE DATABASE $db CHARACTER SET utf8mb4"
gzip -dc "$state/cms.sql.gz" | mysql --max-allowed-packet=64M --protocol=socket -uroot "$db"
mysql --protocol=socket -uroot -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$db' AND table_type='BASE TABLE'" | grep -x 11
mysql --protocol=socket -uroot "$db" -Nse 'SELECT "revisions",COUNT(*) FROM content_revisions UNION ALL SELECT "drafts",COUNT(*) FROM content_drafts UNION ALL SELECT "media",COUNT(*) FROM media_assets'
echo CELIKOM_FRESH_DB_INTAKE_RESTORE_OK
