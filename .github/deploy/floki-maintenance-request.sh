#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only audit; no permission changes.
ctr=celikom-mdb-check-20261122
app=/srv/celikom/app/staging-20261122
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

read -r old_api api_account < <(runuser -u www-data -- php -r 'require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";$p=Celikom\Database\Connection::open($c);$r=$p->query("SELECT DATABASE(),CURRENT_USER()")->fetch(PDO::FETCH_NUM);echo implode(" ",$r),PHP_EOL;' "$app")
[[ "$old_api" =~ ^[A-Za-z0-9_]+$ && "$api_account" =~ ^[A-Za-z0-9_]+@[A-Za-z0-9_.%:-]+$ ]]
u=$(printf '%s' "$api_account" | cut -d@ -f1)
h=$(printf '%s' "$api_account" | cut -d@ -f2)
echo '=== API database privilege audit ==='
api_sql -e "SELECT Db,Select_priv,Insert_priv,Update_priv,Delete_priv,Grant_priv FROM mysql.db WHERE User='$u' AND Host='$h' AND REPLACE(Db,CHAR(92),'') IN ('$old_api','celikom_cutover_20261124') ORDER BY Db"
api_sql -e "SELECT COUNT(*) AS cutover_schema_exists FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='celikom_cutover_20261124'"
mysql --protocol=socket -uroot -e "SELECT COUNT(*) AS cms_cutover_schema_exists FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='celikom_website_cutover_20261124'"
test ! -e /etc/nginx/conf.d/celikom-cutover-probe.conf
for p in /api/v1/health /api/v1/config /admin/; do
  printf '%s ' "$p"
  curl -sS --max-time 10 -o /dev/null -w '%{http_code}\n' "https://api.celikom.com$p"
done
echo CELIKOM_DB_READONLY_AUDIT_OK
