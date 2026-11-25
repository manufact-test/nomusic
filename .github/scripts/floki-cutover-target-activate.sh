#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Executed by owner-approved maintenance gateway after source HTTP writes are frozen.
# On any public activation failure, restore all six active files and reload Nginx.
intake=/root/celikom-cutover-intake
prepared=/root/celikom-cutover-prepared
app=/srv/celikom/app/staging-20261122
site=/srv/celikom-site/celikom-private
api_db=celikom_cutover_20261124
cms_db=celikom_website_cutover_20261124
ctr=celikom-mdb-check-20261122
api_sql(){
 docker exec -i "$ctr" sh -c '
 if [ -n "${MARIADB_ROOT_PASSWORD_FILE:-}" ]; then MYSQL_PWD=$(cat "$MARIADB_ROOT_PASSWORD_FILE")
 elif [ -n "${MYSQL_ROOT_PASSWORD_FILE:-}" ]; then MYSQL_PWD=$(cat "$MYSQL_ROOT_PASSWORD_FILE")
 elif [ -n "${MARIADB_ROOT_PASSWORD:-}" ]; then MYSQL_PWD=$MARIADB_ROOT_PASSWORD
 else exit 2; fi
 export MYSQL_PWD
 exec mariadb -uroot --max-allowed-packet=64M "$@"
 ' sh "$@"
}
cms_sql(){ mysql --protocol=socket -uroot --max-allowed-packet=64M "$@"; }
for kind in api cms; do
 test -f "$intake/$kind.sql.gz" && test ! -L "$intake/$kind.sql.gz"
 gzip -t "$intake/$kind.sql.gz"
done
for name in api-https.conf api-staging.conf site-https.conf website-preview.conf api.env website-staging-config.php; do
 test -f "$prepared/$name" && test ! -L "$prepared/$name"
done
read -r old_api api_account < <(runuser -u www-data -- php -r 'require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";$p=Celikom\Database\Connection::open($c);$r=$p->query("SELECT DATABASE(),CURRENT_USER()")->fetch(PDO::FETCH_NUM);echo implode(" ",$r),PHP_EOL;' "$app")
read -r old_cms cms_account < <(runuser -u celikom-site -- php -r 'require $argv[1]."/app/bootstrap.php";$p=Celikom\Website\Database::connect(Celikom\Website\CmsConfig::databaseSettings());$r=$p->query("SELECT DATABASE(),CURRENT_USER()")->fetch(PDO::FETCH_NUM);echo implode(" ",$r),PHP_EOL;' "$site")
[[ "$old_api" =~ ^[a-zA-Z0-9_]+$ && "$old_cms" =~ ^[a-zA-Z0-9_]+$ ]]
[[ "$api_account" =~ ^[a-zA-Z0-9_]+@[a-zA-Z0-9_.%:-]+$ && "$cms_account" =~ ^[a-zA-Z0-9_]+@[a-zA-Z0-9_.%:-]+$ ]]
[[ "$old_api" != "$api_db" && "$old_cms" != "$cms_db" ]]
[[ "$(api_sql -Nse "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$api_db'")" == 1 ]]
[[ "$(cms_sql -Nse "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$cms_db'")" == 1 ]]
# New SQL is authoritative only after the source write-freeze contract has been checked by the caller.
read -r ac al < <(api_sql -Nse "SELECT DEFAULT_CHARACTER_SET_NAME,DEFAULT_COLLATION_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$old_api'")
read -r cc cl < <(cms_sql -Nse "SELECT DEFAULT_CHARACTER_SET_NAME,DEFAULT_COLLATION_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$old_cms'")
for token in "$ac" "$al" "$cc" "$cl"; do [[ "$token" =~ ^[a-zA-Z0-9_]+$ ]]; done
api_sql -e "DROP DATABASE $api_db; CREATE DATABASE $api_db CHARACTER SET $ac COLLATE $al"
gzip -dc "$intake/api.sql.gz" | api_sql "$api_db"
cms_sql -e "DROP DATABASE $cms_db; CREATE DATABASE $cms_db CHARACTER SET $cc COLLATE $cl"
u=$(printf %s "$cms_account" | cut -d@ -f1)
h=$(printf %s "$cms_account" | cut -d@ -f2-)
privs=$(cms_sql -Nse "SELECT GROUP_CONCAT(PRIVILEGE_TYPE ORDER BY PRIVILEGE_TYPE SEPARATOR ', ') FROM information_schema.SCHEMA_PRIVILEGES WHERE TABLE_SCHEMA='$old_cms' AND GRANTEE=CONCAT(QUOTE('$u'),'@',QUOTE('$h'))")
[[ "$privs" =~ ^[A-Z][A-Z,\ ]+$ && "$privs" != NULL ]]
cms_sql -e "GRANT $privs ON $cms_db.* TO '$u'@'$h'"
gzip -dc "$intake/cms.sql.gz" | cms_sql "$cms_db"
[[ "$(api_sql -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$api_db' AND table_type='BASE TABLE'")" == 44 ]]
[[ "$(cms_sql -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$cms_db' AND table_type='BASE TABLE'")" == 11 ]]
runuser -u www-data -- env DB_NAME="$api_db" php -r '
require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";$p=Celikom\Database\Connection::open($c);
if($p->query("SELECT DATABASE()")->fetchColumn()!==$argv[2])exit(2);
$p->beginTransaction();
try{
 $email="cutover-".bin2hex(random_bytes(12))."@example.invalid";
 $p->prepare("INSERT INTO users(email,password_hash) VALUES (?,?)")->execute([$email,password_hash("test",PASSWORD_DEFAULT)]);
 $id=(int)$p->lastInsertId();if(!$id)exit(2);
 $p->prepare("UPDATE users SET password_hash=? WHERE id=?")->execute([password_hash("updated",PASSWORD_DEFAULT),$id]);
 $s=$p->prepare("DELETE FROM users WHERE id=?");$s->execute([$id]);
 if($s->rowCount()!=1)exit(2);
 $p->rollBack();echo "FINAL_API_RUNTIME_CRUD_ROLLEDBACK",PHP_EOL;
}catch(Throwable $e){if($p->inTransaction())$p->rollBack();throw $e;}
' "$app" "$api_db"
runuser -u celikom-site -- env CELIKOM_SITE_DB_NAME="$cms_db" php -r '
require $argv[1]."/app/bootstrap.php";
$p=Celikom\Website\Database::connect(Celikom\Website\CmsConfig::databaseSettings());
if($p->query("SELECT DATABASE()")->fetchColumn()!==$argv[2])exit(2);
echo "FINAL_CMS_RUNTIME_CONNECTED",PHP_EOL;
' "$site" "$cms_db"
echo FINAL_ISOLATED_DATABASES_READY
# Store independent root-private copies of the live files for immediate rollback.
backup=$(mktemp -d /root/celikom-live-rollback-XXXXXXXX)
check_target(){
 local p=$1
 test -f "$p" && test ! -L "$p" && test "$(stat -c %u "$p")" = 0
}
check_target /etc/nginx/sites-available/celikom-api-https
check_target /etc/nginx/sites-available/celikom-api-staging
check_target /etc/nginx/sites-available/celikom-site-https
check_target /etc/nginx/sites-available/celikom-website-preview
mapfile -t destinations <<'FILES'
/etc/nginx/sites-available/celikom-api-https
/etc/nginx/sites-available/celikom-api-staging
/etc/nginx/sites-available/celikom-site-https
/etc/nginx/sites-available/celikom-website-preview
/srv/celikom/app/staging-20261122/.env
/srv/celikom-site/celikom-private/staging-config.php
FILES
mapfile -t sources <<'FILES'
/root/celikom-cutover-prepared/api-https.conf
/root/celikom-cutover-prepared/api-staging.conf
/root/celikom-cutover-prepared/site-https.conf
/root/celikom-cutover-prepared/website-preview.conf
/root/celikom-cutover-prepared/api.env
/root/celikom-cutover-prepared/website-staging-config.php
FILES
for i in 0 1 2 3 4 5; do
 test -f "${destinations[$i]}" && test ! -L "${destinations[$i]}"
 cp -a "${destinations[$i]}" "$backup/$i"
done
rollback(){
 for i in 0 1 2 3 4 5; do cp -a "$backup/$i" "${destinations[$i]}" || true; done
 nginx -t && systemctl reload nginx || true
 echo CELIKOM_LIVE_ACTIVATION_ROLLED_BACK
}
ok=0
trap 'rc=$?; if [[ "$ok" != 1 ]]; then rollback; fi; exit "$rc"' EXIT
for i in 0 1 2 3 4 5; do
 dest="${destinations[$i]}"
 tmp=$(mktemp "$dest.celikom-XXXXXXXX")
 cat "${sources[$i]}" > "$tmp"
 chown --reference="$dest" "$tmp"
 chmod --reference="$dest" "$tmp"
 mv -f -- "$tmp" "$dest"
done
runuser -u www-data -- php -r 'require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";$p=Celikom\Database\Connection::open($c);if($p->query("SELECT DATABASE()")->fetchColumn()!=="celikom_cutover_20261124")exit(2);echo "FINAL_API_LIVE_DB_SELECTED",PHP_EOL;' "$app"
runuser -u celikom-site -- php -r 'require $argv[1]."/app/bootstrap.php";$p=Celikom\Website\Database::connect(Celikom\Website\CmsConfig::databaseSettings());if($p->query("SELECT DATABASE()")->fetchColumn()!=="celikom_website_cutover_20261124")exit(2);echo "FINAL_CMS_LIVE_DB_SELECTED",PHP_EOL;' "$site"
nginx -t
systemctl reload nginx
[[ "$(curl --silent --show-error --max-time 10 -o /dev/null -w '%{http_code}' https://api.celikom.com/api/v1/health)" == 200 ]]
curl -fsS --max-time 15 https://api.celikom.com/api/v1/config > "$backup/config.json"
python3 - "$backup/config.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); f=v["features"]
assert all(f[k] for k in ("replacements","auth","entitlement","rewards"))
assert not any(f[k] for k in ("analytics","billing_views","referrals"))
assert v["upload_enabled"] is True and v["max_upload_size"]==31457280
print("FINAL_PUBLIC_API_FEATURES_READY")
PY
[[ "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' https://api.celikom.com/api/v1/auth/me)" == 401 ]]
[[ "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' 'https://api.celikom.com/api/v1/resolve?service=yandex&track_id=144530503')" == 401 ]]
admin=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' https://api.celikom.com/admin/)
case "$admin" in 200|301|302|303|401) ;; *) echo "ADMIN_HTTP_UNEXPECTED=$admin"; exit 2 ;; esac
for url in / /admin/ /downloads/windows/CELIKOM-Windows-0.24.55.exe /downloads/extension/celikom-extension-0.4.73.zip /updates/android/stable.json; do
 [[ "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "https://celikom.com$url")" == 401 ]]
done
ok=1
echo "FLOKI_LIVE_ROLLBACK_DIRECTORY=$backup"
echo CELIKOM_PRODUCTION_API_AND_CMS_SWITCH_VERIFIED
