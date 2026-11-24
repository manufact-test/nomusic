#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
state=/root/celikom-cutover-snapshot-YaDz8eHD/intake
[[ ! -e /usr/local/sbin/celikom-cutover-receive && ! -e /etc/sudoers.d/celikom-cutover-receive ]]
for kind in api cms; do
  test -f "$state/$kind.sql.gz" && test ! -L "$state/$kind.sql.gz"
  gzip -t "$state/$kind.sql.gz"
done
printf '%s  %s\n' '795def31faba800bbace2b54c4bc25443e2ee7ec31a6b6cb50163f895b1266a3' "$state/api.sql.gz" '61113119c4436ac7a986e30d59cced4097ef15b1cd64b32a44a0f9aad8141d76' "$state/cms.sql.gz" | sha256sum -c -
echo '=== Restore failure diagnostics (no data) ==='
free -m
journalctl -k --since '2026-11-24 19:09:40 UTC' --until '2026-11-24 19:10:40 UTC' --no-pager | grep -Ei 'oom|out of memory|killed process' || true
gzip -dc "$state/api.sql.gz" | awk 'length>max{max=length} NR==7147{n=length} END{print "SQL_MAX_LINE_BYTES",max,"FAIL_LINE_BYTES",n}'
container="celikom-cutover-restore-$(date +%s)"
db="celikom_cms_cutover_verify_$(date +%s)"
ok=0
cleanup(){
  rc=$?
  if [[ "$ok" != 1 ]]; then
    docker inspect --format 'RESTORE_CONTAINER exit={{.State.ExitCode}} oom={{.State.OOMKilled}} status={{.State.Status}}' "$container" 2>/dev/null || true
    docker logs "$container" 2>&1 | grep -Ei 'entrypoint|ready for connections|error|shutdown|aborted' | tail -n 25 || true
  fi
  docker rm -f "$container" >/dev/null 2>&1 || true
  mysql --protocol=socket -uroot -e "DROP DATABASE IF EXISTS $db" >/dev/null 2>&1 || true
  exit "$rc"
}
trap cleanup EXIT
docker run --pull=never --network none --name "$container" -e MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1 -d mariadb:11.8.9-noble --innodb-buffer-pool-size=64M --max-allowed-packet=64M --max-connections=8 --performance-schema=OFF >/dev/null
ready=0
# Do not connect to the entrypoint's transient bootstrap server.
for i in $(seq 1 90); do
  if docker logs "$container" 2>&1 | grep -F 'MariaDB init process done. Ready for start up.' >/dev/null && docker exec "$container" mariadb -uroot -Nse 'SELECT 1' >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
[[ "$ready" == 1 ]]
echo RESTORE_FINAL_MARIADB_READY
docker exec "$container" mariadb -uroot -e 'CREATE DATABASE celikom_restore CHARACTER SET utf8mb4'
gzip -dc "$state/api.sql.gz" | docker exec -i "$container" mariadb --max-allowed-packet=64M -uroot celikom_restore
docker exec "$container" mariadb -uroot -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='celikom_restore' AND table_type='BASE TABLE'" | grep -x 44
docker exec "$container" mariadb -uroot celikom_restore -Nse 'SELECT "tracks",COUNT(*) FROM tracks UNION ALL SELECT "audio_assets",COUNT(*) FROM audio_assets UNION ALL SELECT "replacements",COUNT(*) FROM track_replacements UNION ALL SELECT "users",COUNT(*) FROM users UNION ALL SELECT "sessions",COUNT(*) FROM user_sessions'
echo API_FRESH_RESTORE_OK
mysql --protocol=socket -uroot -e "CREATE DATABASE $db CHARACTER SET utf8mb4"
gzip -dc "$state/cms.sql.gz" | mysql --max-allowed-packet=64M --protocol=socket -uroot "$db"
mysql --protocol=socket -uroot -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$db' AND table_type='BASE TABLE'" | grep -x 11
mysql --protocol=socket -uroot "$db" -Nse 'SELECT "revisions",COUNT(*) FROM content_revisions UNION ALL SELECT "drafts",COUNT(*) FROM content_drafts UNION ALL SELECT "media",COUNT(*) FROM media_assets'
ok=1
echo CELIKOM_FRESH_DB_INTAKE_RESTORE_OK
