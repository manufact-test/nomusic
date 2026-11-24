#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/app/staging-20261122
echo '=== Runtime config keys only ==='
runuser -u www-data -- php -r '$c=require $argv[1]; echo implode("\n",array_keys($c)),"\n";' "$S/config/app.php"
echo '=== DB schema existence check only; no row data ==='
runuser -u www-data -- php -r '
require $argv[1]."/bootstrap.php";
$c=require $argv[1]."/config/app.php";
$dsn="mysql:host=".$c["db_host"].";port=".($c["db_port"]??3306).";dbname=".$c["db_name"].";charset=utf8mb4";
$p=new PDO($dsn,$c["db_user"],$c["db_password"],[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);
foreach (["bulk_moderation_tombstones","track_replacements","audio_assets","tracks"] as $t) {
 $q=$p->prepare("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=?");
 $q->execute([$t]); echo "TABLE_",$t,"=",$q->fetchColumn(),"\n";
}
$q=$p->query("SELECT column_name,data_type,is_nullable FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=\x27bulk_moderation_tombstones\x27 ORDER BY ordinal_position");
foreach($q->fetchAll(PDO::FETCH_ASSOC) as $r) echo "COLUMN ",$r["column_name"]," ",$r["data_type"]," nullable=",$r["is_nullable"],"\n";
' "$S"
echo CELIKOM_BULK_MODERATION_DB_SCHEMA_CHECK_OK
