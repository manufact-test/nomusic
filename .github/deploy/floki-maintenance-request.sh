#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
S=/srv/celikom/app/staging-20261122
echo '=== Migration tracker structure and applied migration tail ==='
runuser -u www-data -- php -r '
require $argv[1]."/bootstrap.php"; $c=require $argv[1]."/config/app.php";
$p=new PDO("mysql:host=".$c["db_host"].";port=".$c["db_port"].";dbname=".$c["db_name"].";charset=utf8mb4",$c["db_user"],$c["db_password"],[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION]);
$r=$p->query("SHOW CREATE TABLE schema_migrations")->fetch(PDO::FETCH_NUM); echo $r[1],"\n";
foreach($p->query("SELECT * FROM schema_migrations ORDER BY 1 DESC LIMIT 5")->fetchAll(PDO::FETCH_ASSOC) as $row) echo "APPLIED_META ",json_encode($row,JSON_UNESCAPED_SLASHES),"\n";
' "$S"
echo '=== Validator file modes at both imported copies ==='
for f in /srv/celikom/app/staging-20261122/tools/mp3-validator /srv/celikom/migration/hostinger-import/live-release/tools/mp3-validator; do
 if [[ -e "$f" ]]; then stat -c '%n mode=%a owner=%U:%G size=%s' "$f"; sha256sum "$f"; fi
done
runuser -u www-data -- php -r '$p=$argv[1]; echo "STAGING_MP3_VALIDATOR_EXECUTABLE=",is_executable($p)?"yes":"no","\n";' "$S/tools/mp3-validator"
echo '=== MP3 validator embedded build strings (static read only) ==='
python3 - "$S/tools/mp3-validator" <<'PY'
import pathlib,re,sys
b=pathlib.Path(sys.argv[1]).read_bytes()
ss=[x.decode("ascii","ignore") for x in re.findall(rb"[\x20-\x7e]{8,}",b)]
for s in ss:
 if re.search(r"ffmpeg version|configuration:|libavcodec|libavformat|libavutil|LAME|LGPL|GPL|Copyright",s,re.I):
  print(s[:1000])
PY
echo '=== FFmpeg source license and version metadata ==='
tar -xOzf "$S/tools/source.tar.gz" FFmpeg-2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99/LICENSE.md > /tmp/celikom-ffmpeg-license.txt
sed -n '1,100p' /tmp/celikom-ffmpeg-license.txt
tar -xOzf "$S/tools/source.tar.gz" FFmpeg-2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99/RELEASE > /tmp/celikom-ffmpeg-release.txt
cat /tmp/celikom-ffmpeg-release.txt
echo '=== Bulk moderation test and migration source search ==='
find "$S" -type f \( -iname '*bulk*test*' -o -iname '*moderation*test*' -o -iname '*mp3*test*' \) -printf '%P\n' | sort
grep -RIl 'bulk_moderation_tombstones' "$S/migrations" "$S/tests" 2>/dev/null || true
echo CELIKOM_MIGRATION_MP3_EXEC_AND_LICENSE_CHECK_OK
