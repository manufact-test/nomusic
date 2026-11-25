#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Post-cutover encrypted, additive recovery delta.  Do not expose SQL/keys in
# Git, Actions artifacts, stdout, or public web routes.
basedir=/srv/celikom/migration
key="$basedir/secrets/celikom-offsite-20261122.key"
root="$basedir/final-delta-20261125-v2"
out="$basedir/backups/celikom-final-delta-20261125-v2.tar.gpg"
work="$root/plain"
recovery="$root/restore-test"
ctr=celikom-mdb-check-20261122
api_db=celikom_cutover_20261124
cms_db=celikom_website_cutover_20261124
scratch_cms=celikom_final_recovery_20261125_v2
scratch_ctr=celikom-final-recovery-20261125-v2
[[ ! -e "$root" && ! -L "$root" && ! -e "$out" && ! -L "$out" ]]
[[ -f "$key" && ! -L "$key" && "$(stat -c %u "$key")" == 0 ]]
[[ "$(stat -c %a "$key")" == 600 || "$(stat -c %a "$key")" == 400 ]]
[[ "$(df -B1 --output=avail "$basedir" | tail -1)" -gt 16000000000 ]]
[[ "$(docker ps --filter "name=^/$scratch_ctr$" --format '{{.Names}}' | wc -l)" == 0 ]]
[[ "$(mysql --protocol=socket -uroot -Nse "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$scratch_cms'")" == 0 ]]
install -d -m 700 "$root" "$work" "$work/sql" "$work/config" "$work/releases" "$recovery"
made_ctr=0
made_cms=0
complete=0
clean(){
 rc=$?
 if [[ "$made_ctr" == 1 ]]; then docker rm -f "$scratch_ctr" >/dev/null 2>&1 || rc=1; fi
 if [[ "$made_cms" == 1 ]]; then mysql --protocol=socket -uroot -e "DROP DATABASE IF EXISTS $scratch_cms" || rc=1; fi
 rm -rf -- "$work" "$recovery"
 if [[ "$complete" != 1 ]]; then
   echo CELIKOM_FINAL_DELTA_BACKUP_ABORTED_NO_PRODUCTION_MUTATION
 fi
 exit "$rc"
}
trap clean EXIT

api_dump(){
 docker exec -i "$ctr" sh -c '
   if [ -n "$MARIADB_ROOT_PASSWORD_FILE" ]; then MYSQL_PWD=$(cat "$MARIADB_ROOT_PASSWORD_FILE")
   elif [ -n "$MYSQL_ROOT_PASSWORD_FILE" ]; then MYSQL_PWD=$(cat "$MYSQL_ROOT_PASSWORD_FILE")
   elif [ -n "$MARIADB_ROOT_PASSWORD" ]; then MYSQL_PWD=$MARIADB_ROOT_PASSWORD
   else exit 2; fi
   export MYSQL_PWD
   exec mariadb-dump -uroot --single-transaction --quick --triggers --routines --events --max-allowed-packet=64M "$@"
 ' sh "$@"
}
runuser -u www-data -- php -r 'require "/srv/celikom/app/staging-20261122/bootstrap.php";$c=require "/srv/celikom/app/staging-20261122/config/app.php";$p=Celikom\Database\Connection::open($c);if($p->query("SELECT DATABASE()")->fetchColumn()!=="celikom_cutover_20261124")exit(2);echo "BACKUP_SOURCE_LIVE_API_DB_CONFIRMED\n";'
runuser -u celikom-site -- php -r 'require "/srv/celikom-site/celikom-private/app/bootstrap.php";$p=Celikom\Website\Database::connect(Celikom\Website\CmsConfig::databaseSettings());if($p->query("SELECT DATABASE()")->fetchColumn()!=="celikom_website_cutover_20261124")exit(2);echo "BACKUP_SOURCE_LIVE_CMS_DB_CONFIRMED\n";'

api_dump "$api_db" | gzip -n -6 > "$work/sql/api.sql.gz"
mysqldump --protocol=socket -uroot --single-transaction --quick --triggers --routines --events --set-gtid-purged=OFF --no-tablespaces "$cms_db" | gzip -n -6 > "$work/sql/cms.sql.gz"
for kind in api cms; do [[ -s "$work/sql/$kind.sql.gz" ]]; gzip -t "$work/sql/$kind.sql.gz"; done
echo CELIKOM_POST_CUTOVER_LIVE_SQL_DUMPS_COMPLETE

copy_secure(){
 src=$1
 target=$2
 [[ -f "$src" && ! -L "$src" && -r "$src" ]]
 [[ "$(stat -c %a "$src")" =~ ^(600|640|644)$ ]]
 install -m 600 "$src" "$work/$target"
}
copy_secure /srv/celikom/app/staging-20261122/.env config/api.env
copy_secure /srv/celikom-site/celikom-private/staging-config.php config/cms-staging-config.php
copy_secure /etc/nginx/sites-available/celikom-api-https config/api-public-nginx.conf
copy_secure /etc/nginx/sites-available/celikom-api-staging config/api-upstream-nginx.conf
copy_secure /etc/nginx/sites-available/celikom-site-https config/cms-public-nginx.conf
copy_secure /etc/nginx/sites-available/celikom-website-preview config/cms-upstream-nginx.conf
copy_secure /etc/nginx/celikom-site.htpasswd config/cms-htpasswd
copy_secure /srv/celikom-releases/private/android-v95/CELIKOM-Android-0.3.94-SIGNED.apk releases/android-v95-signed.apk
copy_secure /srv/celikom-releases/private/android-v95/stable-floki-candidate.json releases/android-v95-floki.json
copy_secure /srv/celikom-releases/private/android-v95/stable-hostinger-bridge-candidate.json releases/android-v95-hostinger-bridge.json
copy_secure /srv/celikom-releases/private/extension/celikom-extension-0.4.73.zip releases/extension-0.4.73.zip

python3 - "$work" <<'PY'
import json,pathlib,hashlib,datetime,sys
root=pathlib.Path(sys.argv[1])
files=[p for p in root.rglob('*') if p.is_file() and p.name not in ('metadata.json','SHA256SUMS')]
files.sort(key=lambda p:p.relative_to(root).as_posix())
manifest={
 "format":"CELIKOM-final-postcutover-delta-recovery-v1",
 "utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "live_api_db":"celikom_cutover_20261124",
 "live_cms_db":"celikom_website_cutover_20261124",
 "base_offsite_ciphertext_sha256":"9d94a07d3306acd8874a7d3ad959234427d67a0d1b9c402526abb492e3acff15",
 "base_archive_owner_offsite_copy_required":True,
 "owner_offsite_delta_download_required":True,
 "media_audio_manifest_digest":"9240eeba545d433d2fec25690c8d740de729d614db4c28f40ca91bea6b6c24ed",
 "cms_media_manifest_digest":"567dddbeb64aa8707bf9d54f9569313685652d058f6731cee06c3e2acecd9ed6",
 "files":{p.relative_to(root).as_posix():{
     "bytes":p.stat().st_size,
     "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
 } for p in files}
}
(root/'metadata.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
with (root/'SHA256SUMS').open('w') as f:
  for p in files:
    f.write(manifest['files'][p.relative_to(root).as_posix()]['sha256']+'  '+p.relative_to(root).as_posix()+'\n')
  f.write(hashlib.sha256((root/'metadata.json').read_bytes()).hexdigest()+'  metadata.json\n')
print("CELIKOM_FINAL_DELTA_PLAIN_INPUT_FILES",len(files))
PY
(cd "$work" && sha256sum --check SHA256SUMS --status)
# Reuse the recovery secret that is already in the owner's offline custody.
# Ciphertext is the only persistent backup output; no plaintext root copy.
(
  cd "$work"
  tar -cf - . | gpg --batch --yes --no-tty --pinentry-mode loopback \
    --passphrase-file "$key" --symmetric --cipher-algo AES256 \
    --compress-algo none --output "$out"
)
[[ -s "$out" && ! -L "$out" ]]
chmod 600 "$out"
echo CELIKOM_FINAL_DELTA_AES256_ENCRYPTED_ARCHIVE_CREATED

# Full independent decryption and safe extraction into a disposable private tree.
install -d -m 700 "$recovery/tree" "$recovery/gnupg"
cat > "$root/safe-restore.py" <<'PY'
import tarfile,sys,pathlib
root=pathlib.Path(sys.argv[1])
count=0
with tarfile.open(fileobj=sys.stdin.buffer,mode="r|*") as tar:
  for member in tar:
    count+=1
    if count>70: raise ValueError("Unexpected backup member count")
    if not (member.isfile() or member.isdir()): raise ValueError("Recovery archive has link or device")
    if member.isfile() and member.size>200*1024*1024: raise ValueError("Unexpected member size")
    tar.extract(member,root,filter='data')
assert count>=10,count
print("CELIKOM_FINAL_DELTA_SAFE_ARCHIVE_MEMBERS",count)
PY
gpg --homedir "$recovery/gnupg" --batch --no-tty --pinentry-mode loopback \
  --passphrase-file "$key" --decrypt "$out" 2>/dev/null | python3 "$root/safe-restore.py" "$recovery/tree"

restored="$recovery/tree"
(cd "$restored" && sha256sum -c SHA256SUMS --status)
python3 - "$restored" <<'PY'
import pathlib,json,hashlib,sys
root=pathlib.Path(sys.argv[1])
m=json.loads((root/'metadata.json').read_bytes())
assert m['format']=='CELIKOM-final-postcutover-delta-recovery-v1'
assert m['live_api_db']=='celikom_cutover_20261124'
assert m['live_cms_db']=='celikom_website_cutover_20261124'
assert len(m['files'])>=10
for relative,record in m['files'].items():
 p=root/relative
 assert p.is_file() and p.stat().st_size==record['bytes']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
print("CELIKOM_FINAL_DELTA_ENCRYPTED_ROUNDTRIP_BYTES_MATCH")
PY
for kind in api cms; do gzip -t "$restored/sql/$kind.sql.gz"; done

# Isolated MariaDB11 image has no network, no volumes and no production grants.
docker run --pull=never --network none --name "$scratch_ctr" \
  -e MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1 \
  -d mariadb:11.8.9-noble \
  --innodb-buffer-pool-size=64M --max-allowed-packet=64M \
  --max-connections=8 --performance-schema=OFF >/dev/null
made_ctr=1
ready=0
for i in $(seq 1 90); do
 if docker logs "$scratch_ctr" 2>&1 | grep -Fq 'MariaDB init process done. Ready for start up.' \
    && docker exec "$scratch_ctr" mariadb -uroot -Nse 'SELECT 1' >/dev/null 2>&1; then
  ready=1; break
 fi
 sleep 1
done
[[ "$ready" == 1 ]]
docker exec "$scratch_ctr" mariadb -uroot -e 'CREATE DATABASE celikom_backup_test'
gzip -dc "$restored/sql/api.sql.gz" | docker exec -i "$scratch_ctr" mariadb -uroot --max-allowed-packet=64M celikom_backup_test
docker exec "$scratch_ctr" mariadb -uroot celikom_backup_test -Nse "SELECT 'API_TABLES',COUNT(*) FROM information_schema.tables WHERE table_schema='celikom_backup_test' AND table_type='BASE TABLE'; SELECT 'TRACKS',COUNT(*) FROM tracks; SELECT 'REPLACEMENTS',COUNT(*) FROM track_replacements"
[[ "$(docker exec "$scratch_ctr" mariadb -uroot celikom_backup_test -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='celikom_backup_test' AND table_type='BASE TABLE'")" == 44 ]]
echo CELIKOM_FINAL_DELTA_API_SQL_INDEPENDENT_RESTORE_OK

# MySQL CMS restore into a temporary, isolated schema. No live schema changes.
mysql --protocol=socket -uroot -e "CREATE DATABASE $scratch_cms"
made_cms=1
gzip -dc "$restored/sql/cms.sql.gz" | mysql --protocol=socket -uroot "$scratch_cms"
[[ "$(mysql --protocol=socket -uroot -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$scratch_cms' AND table_type='BASE TABLE'")" == 11 ]]
echo CELIKOM_FINAL_DELTA_CMS_SQL_INDEPENDENT_RESTORE_OK
size=$(stat -c %s "$out")
sha=$(sha256sum "$out" | cut -d' ' -f1)
echo "CELIKOM_FINAL_DELTA_CIPHERTEXT_SIZE=$size"
echo "CELIKOM_FINAL_DELTA_CIPHERTEXT_SHA256=$sha"
complete=1
echo CELIKOM_FINAL_DELTA_ENCRYPTED_RESTORE_TEST_ACCEPTED_NEEDS_OWNER_OFFSITE_COPY
