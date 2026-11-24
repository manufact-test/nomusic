#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/app/staging-20261122
echo '=== MP3 validator PHP wrapper ==='
sed -n '1,180p' "$S/src/Application/Mp3DecodeValidator.php"
echo '=== MP3 normalizer remaining implementation ==='
sed -n '100,260p' "$S/src/Application/Mp3Normalizer.php"
echo '=== Bulk moderation view and browser code ==='
sed -n '1,220p' "$S/src/Admin/BulkModerationView.php"
sed -n '1,180p' "$S/src/Admin/bulk-moderation.js"
echo '=== Exact tombstone table schema ==='
runuser -u www-data -- php -r '
require $argv[1]."/bootstrap.php"; $c=require $argv[1]."/config/app.php";
$p=new PDO("mysql:host=".$c["db_host"].";port=".$c["db_port"].";dbname=".$c["db_name"].";charset=utf8mb4",$c["db_user"],$c["db_password"],[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);
$r=$p->query("SHOW CREATE TABLE bulk_moderation_tombstones")->fetch(PDO::FETCH_NUM);
echo $r[1],"\n";
$q=$p->query("SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema=DATABASE() AND (TABLE_NAME LIKE \'%migration%\' OR TABLE_NAME LIKE \'%schema%\') ORDER BY TABLE_NAME");
foreach($q->fetchAll(PDO::FETCH_COLUMN) as $t) echo "META_TABLE ",$t,"\n";
' "$S"
echo '=== Migration inventory and tombstone references ==='
find "$S/migrations" -maxdepth 1 -type f -printf '%f\n' | sort
grep -RIl 'bulk_moderation_tombstones' /srv/celikom /root/celikom-cutover-prepared 2>/dev/null | head -n 30 > /tmp/celikom-bulk-migration-hits.txt || true
cat /tmp/celikom-bulk-migration-hits.txt
echo '=== Validator and source archive licensing markers ==='
strings "$S/tools/mp3-validator" > /tmp/celikom-validator-strings.txt
grep -Ei -m 25 'ffmpeg version|configuration:|libavcodec|libavformat|libavutil|LAME|LGPL|GPL|Copyright' /tmp/celikom-validator-strings.txt || true
tar -xOzf "$S/tools/source.tar.gz" FFmpeg-2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99/LICENSE.md > /tmp/celikom-ffmpeg-license.txt
sed -n '1,100p' /tmp/celikom-ffmpeg-license.txt
echo CELIKOM_BULK_SCHEMA_AND_MP3_RUNTIME_REVIEW_OK
