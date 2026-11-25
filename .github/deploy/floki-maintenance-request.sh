#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Prepare isolated cutover schemas and verify real FPM requests; no public change.
snapshot=/root/celikom-cutover-snapshot-YaDz8eHD/intake
# Immutable transferred SQL snapshots; no Hostinger mutation.
for kind in api cms; do
  test -f "$snapshot/$kind.sql.gz" && test ! -L "$snapshot/$kind.sql.gz"
  gzip -t "$snapshot/$kind.sql.gz"
done
printf '%s  %s\n' \
 '795def31faba800bbace2b54c4bc25443e2ee7ec31a6b6cb50163f895b1266a3' "$snapshot/api.sql.gz" \
 '61113119c4436ac7a986e30d59cced4097ef15b1cd64b32a44a0f9aad8141d76' "$snapshot/cms.sql.gz" | sha256sum --check --status
echo CUTOVER_SNAPSHOT_HASHES_OK
prep=/root/celikom-cutover-prepared
app=/srv/celikom/app/staging-20261122
site=/srv/celikom-site/celikom-private
ctr=celikom-mdb-check-20261122
api_db=celikom_cutover_20261124
cms_db=celikom_website_cutover_20261124
live=$(readlink -f /etc/nginx/sites-enabled/celikom-api-staging)
[[ "$live" == /etc/nginx/sites-available/* && -f "$live" ]]
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
api_sql -Nse 'SELECT 1' | grep -x 1
cms_sql -Nse 'SELECT 1' | grep -x 1
read -r old_api api_account < <(runuser -u www-data -- php -r 'require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";$p=Celikom\Database\Connection::open($c);$r=$p->query("SELECT DATABASE(),CURRENT_USER()")->fetch(PDO::FETCH_NUM);echo implode(" ",$r),PHP_EOL;' "$app")
read -r old_cms cms_account < <(runuser -u celikom-site -- php -r 'require $argv[1]."/app/bootstrap.php";$p=Celikom\Website\Database::connect(Celikom\Website\CmsConfig::databaseSettings());$r=$p->query("SELECT DATABASE(),CURRENT_USER()")->fetch(PDO::FETCH_NUM);echo implode(" ",$r),PHP_EOL;' "$site")
for db in "$old_api" "$old_cms"; do [[ "$db" =~ ^[A-Za-z0-9_]+$ ]]; done
for account in "$api_account" "$cms_account"; do [[ "$account" =~ ^[A-Za-z0-9_]+@[A-Za-z0-9_.%:-]+$ ]]; done
[[ "$old_api" != "$api_db" && "$old_cms" != "$cms_db" ]]
[[ "$(api_sql -Nse "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$api_db'")" == 0 ]]
[[ "$(cms_sql -Nse "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$cms_db'")" == 0 ]]
backup=$(mktemp -d /root/celikom-cutover-stage-XXXXXXXX)
cp -a "$live" "$backup/live"
cp -a "$prep/api.env" "$backup/api.env"
probe=/etc/nginx/conf.d/celikom-cutover-probe.conf
[[ ! -e "$probe" && ! -L "$probe" ]]
made_api=0; made_cms=0; probe_on=0; ok=0
cleanup(){
  rc=$?
  if [[ "$probe_on" == 1 ]]; then
    rm -f "$probe"
    nginx -t && systemctl reload nginx || true
  fi
  if [[ "$ok" != 1 ]]; then
    cp -a "$backup/api.env" "$prep/api.env"
    rm -f "$prep/website-staging-config.php"
    if [[ "$made_api" == 1 ]]; then api_sql -e "DROP DATABASE IF EXISTS $api_db" || true; fi
    if [[ "$made_cms" == 1 ]]; then cms_sql -e "DROP DATABASE IF EXISTS $cms_db" || true; fi
    echo CELIKOM_CUTOVER_STAGE_ROLLBACK
  fi
  rm -f "$backup/login.json" "$backup/refresh.json" "$backup/resolve.json" "$backup/response.json" "$backup/range.bin" "$backup/url"
  exit "$rc"
}
trap cleanup EXIT
mirror_schema(){
  local fn=$1 old=$2 new=$3 account=$4 user host privs charset coll
  user=${account%@*}; host=${account#*@}
  read -r charset coll < <("$fn" -Nse "SELECT DEFAULT_CHARACTER_SET_NAME,DEFAULT_COLLATION_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$old'")
  [[ "$charset" =~ ^[A-Za-z0-9_]+$ && "$coll" =~ ^[A-Za-z0-9_]+$ ]]
  privs=$("$fn" -Nse "SELECT GROUP_CONCAT(PRIVILEGE_TYPE ORDER BY PRIVILEGE_TYPE SEPARATOR ', ') FROM information_schema.SCHEMA_PRIVILEGES WHERE TABLE_SCHEMA='$old' AND GRANTEE=CONCAT(QUOTE('$user'),'@',QUOTE('$host'))")
  [[ "$privs" =~ ^[A-Z][A-Z,\ ]+$ && "$privs" != NULL ]]
  "$fn" -e "CREATE DATABASE $new CHARACTER SET $charset COLLATE $coll"
  if [[ "$fn" == api_sql ]]; then made_api=1; else made_cms=1; fi
  # The API candidate already has exact CRUD grants confirmed by the real app's SHOW GRANTS.
  # Do not attempt a new API grant or alter its identity. CMS still mirrors existing privileges.
  if [[ "$fn" == cms_sql ]]; then
    "$fn" -e "GRANT $privs ON $new.* TO '$user'@'$host'"
  fi
}
mirror_schema api_sql "$old_api" "$api_db" "$api_account"
mirror_schema cms_sql "$old_cms" "$cms_db" "$cms_account"
gzip -dc "$snapshot/api.sql.gz" | api_sql "$api_db"
gzip -dc "$snapshot/cms.sql.gz" | cms_sql "$cms_db"
[[ "$(api_sql -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$api_db' AND table_type='BASE TABLE'")" == 44 ]]
[[ "$(cms_sql -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$cms_db' AND table_type='BASE TABLE'")" == 11 ]]
runuser -u www-data -- env DB_NAME="$api_db" php -r 'require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";$p=Celikom\Database\Connection::open($c);if($p->query("SELECT DATABASE()")->fetchColumn()!==$argv[2])exit(2);echo "API_CANDIDATE_DB_CONNECTED",PHP_EOL;' "$app" "$api_db"
runuser -u celikom-site -- env CELIKOM_SITE_DB_NAME="$cms_db" php -r 'require $argv[1]."/app/bootstrap.php";$p=Celikom\Website\Database::connect(Celikom\Website\CmsConfig::databaseSettings());if($p->query("SELECT DATABASE()")->fetchColumn()!==$argv[2])exit(2);echo "CMS_CANDIDATE_DB_CONNECTED",PHP_EOL;' "$site" "$cms_db"
python3 - "$prep/api.env" "$api_db" "$live" "$probe" "$app" <<'PY'
import pathlib,re,sys
env=pathlib.Path(sys.argv[1]); db=sys.argv[2]; live=pathlib.Path(sys.argv[3]); probe=pathlib.Path(sys.argv[4]); app=sys.argv[5]
data=env.read_text()
data,n=re.subn(r"(?m)^\s*DB_NAME\s*=.*$", "DB_NAME="+db, data)
assert n==1
env.write_text(data)
params=[]
for k in ["FEATURE_ADMIN","FEATURE_REPLACEMENTS","FEATURE_USER_AUTH","FEATURE_USER_ENTITLEMENT","FEATURE_OWNER_UPLOADS","FEATURE_UPLOADS","FEATURE_REWARD_ELIGIBILITY","CELIKOM_APP_DEBUG","FEATURE_ANALYTICS","FEATURE_BILLING_VIEWS","FEATURE_PAID_ENTITLEMENT","FEATURE_REFERRAL_ATTRIBUTION","FEATURE_OWNER_REPORTS"]:
    m=re.search(r"(?m)^\s*"+k+r"=([01])\s*$",data); assert m,k
    params.append("        fastcgi_param "+k+" "+m.group(1)+";")
p=re.findall(r"(?m)^\s*fastcgi_pass\s+([^;\n]+);",live.read_text());assert len(p)==1
assert re.fullmatch(r"unix:/run/php/[A-Za-z0-9_.-]+\.sock|127\.0\.0\.1:\d+",p[0])
probe.write_text("""server {
    listen 127.0.0.1:18082;
    server_name localhost;
    access_log off;
    client_max_body_size 32m;
    location / {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME """+app+"""/public/index.php;
        fastcgi_param HTTPS on;
        fastcgi_param HTTP_AUTHORIZATION $http_authorization;
        fastcgi_param DB_NAME """+db+""";
        fastcgi_param PHP_ADMIN_VALUE "upload_max_filesize=30M\\npost_max_size=32M\\nmax_execution_time=120";
"""+'\n'.join(params)+"""
        fastcgi_pass """+p[0]+""";
        fastcgi_read_timeout 120s;
    }
}
""")
PY
php -r '$a=require $argv[1];if(!is_array($a)||!isset($a["CELIKOM_SITE_DB_NAME"]))exit(2);$a["CELIKOM_SITE_DB_NAME"]=$argv[2];file_put_contents($argv[3],"<?php\nreturn ".var_export($a,true).";\n");' "$site/staging-config.php" "$cms_db" "$prep/website-staging-config.php"
chmod 600 "$prep/api.env" "$prep/website-staging-config.php"
probe_on=1
nginx -t
systemctl reload nginx
base=http://127.0.0.1:18082
for i in $(seq 1 15); do
  if curl -fsS --max-time 3 "$base/api/v1/health" >/dev/null; then break; fi
  sleep 1
done
curl -fsS "$base/api/v1/config" > "$backup/response.json"
python3 - "$backup/response.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]));f=v["features"]
assert f["replacements"] and f["auth"] and f["entitlement"] and f["rewards"] and v["upload_enabled"]
assert not f["analytics"] and not f["billing_views"] and not f["referrals"]
assert v["max_upload_size"]==31457280
print("CANDIDATE_HTTP_FEATURES_OK")
PY
[[ "$(curl -sS -o /dev/null -w '%{http_code}' "$base/api/v1/auth/me")" == 401 ]]
[[ "$(curl -sS -o /dev/null -w '%{http_code}' "$base/api/v1/resolve?service=yandex&track_id=144530503")" == 401 ]]
# Synthetic verified user exists only in the isolated rehearsal schema; never email it.
email="cutover-$(openssl rand -hex 8)@example.invalid"
password=$(openssl rand -hex 24)
installation=$(cat /proc/sys/kernel/random/uuid)
runuser -u www-data -- env DB_NAME="$api_db" php -r 'require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";$p=Celikom\Database\Connection::open($c);if($p->query("SELECT DATABASE()")->fetchColumn()!==$argv[2])exit(2);$p->prepare("INSERT INTO users (email,password_hash) VALUES (?,?)")->execute([$argv[3],password_hash($argv[4],PASSWORD_DEFAULT)]);$id=$p->lastInsertId();$p->prepare("INSERT INTO user_email_security (user_id,verified_at) VALUES (?,UTC_TIMESTAMP(6))")->execute([$id]);' "$app" "$api_db" "$email" "$password"
python3 - "$email" "$password" "$installation" <<'PY' | curl -fsS -H 'Content-Type: application/json' --data-binary @- "$base/api/v1/auth/login" > "$backup/login.json"
import json,sys
print(json.dumps(dict(email=sys.argv[1],password=sys.argv[2],installation_id=sys.argv[3])))
PY
access=$(python3 -c 'import json,sys;v=json.load(open(sys.argv[1]));assert len(v["access_token"])==64;print(v["access_token"])' "$backup/login.json")
curl -fsS -H "Authorization: Bearer $access" -H 'Content-Type: application/json' -d '{}' "$base/api/v1/auth/activate" >/dev/null
python3 - "$backup/login.json" "$installation" <<'PY' | curl -fsS -H 'Content-Type: application/json' --data-binary @- "$base/api/v1/auth/refresh" > "$backup/refresh.json"
import json,sys
v=json.load(open(sys.argv[1]));print(json.dumps(dict(installation_id=sys.argv[2],refresh_token=v["refresh_token"])))
PY
[[ "$(curl -sS -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $access" "$base/api/v1/auth/me")" == 401 ]]
access=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["access_token"])' "$backup/refresh.json")
curl -fsS -H "Authorization: Bearer $access" "$base/api/v1/auth/me" >/dev/null
echo CANDIDATE_HTTP_AUTH_REFRESH_OK
curl -fsS -H "Authorization: Bearer $access" "$base/api/v1/resolve?service=yandex&track_id=144530503&audio_formats=mp3,m4a" > "$backup/resolve.json"
python3 - "$backup/resolve.json" "$backup/url" <<'PY'
import json,sys,urllib.parse
v=json.load(open(sys.argv[1]));assert v.get("found") is True
u=urllib.parse.urlsplit(v["audio_url"]);assert u.path.startswith("/api/v1/audio/") and u.query
open(sys.argv[2],"w").write(u.path+"?"+u.query)
PY
audio_url=$(cat "$backup/url")
[[ "$(curl -sS --max-time 20 -o "$backup/range.bin" -w '%{http_code}' -H 'Range: bytes=0-127' "$base$audio_url")" == 206 ]]
[[ "$(stat -c %s "$backup/range.bin")" == 128 ]]
echo CANDIDATE_HTTP_RESOLVE_SIGNED_RANGE_OK
rm -f "$probe"
nginx -t
systemctl reload nginx
probe_on=0
# Re-import exact snapshot to remove every synthetic account/session/rate-limit change.
api_sql -e "DROP DATABASE $api_db"
made_api=0
mirror_schema api_sql "$old_api" "$api_db" "$api_account"
gzip -dc "$snapshot/api.sql.gz" | api_sql "$api_db"
[[ "$(api_sql -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$api_db' AND table_type='BASE TABLE'")" == 44 ]]
[[ "$(api_sql -Nse "SELECT COUNT(*) FROM $api_db.users WHERE email LIKE 'cutover-%@example.invalid'")" == 0 ]]
[[ "$(curl -sS -o /dev/null -w '%{http_code}' https://api.celikom.com/admin/)" == 404 ]]
ok=1
echo CELIKOM_CUTOVER_SCHEMAS_AND_PRIVATE_HTTP_READY_NOV25
