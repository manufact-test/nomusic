#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only target reconciliation. No live traffic or database modifications.
app=/srv/celikom/app/staging-20261122
runuser -u www-data -- php -r '

function fingerprint(PDO $p, string $kind): void {
 $p->setAttribute(PDO::ATTR_STRINGIFY_FETCHES,true);
 $tables=$p->query("SHOW FULL TABLES WHERE Table_type=\"BASE TABLE\"")->fetchAll(PDO::FETCH_COLUMN);
 sort($tables,SORT_STRING);
 foreach($tables as $t){
  if(!preg_match("/^[a-zA-Z0-9_]+$/D",$t))throw new RuntimeException("Unexpected table");
  $q=$p->query("SELECT * FROM `".$t."`");
  $rows=[];
  while(($row=$q->fetch(PDO::FETCH_NUM))!==false){
   $h=hash_init("sha256");
   foreach($row as $v){
    if($v===null)hash_update($h,"N;");
    else {$v=(string)$v;hash_update($h,"V".strlen($v).":".$v);}
   }
   $rows[]=hash_final($h);
  }
  sort($rows,SORT_STRING);
  echo "FINGERPRINT ",$kind," ",$t," ",count($rows)," ",hash("sha256",implode("\n",$rows)),PHP_EOL;
 }
}

require $argv[1]."/bootstrap.php";$c=require $argv[1]."/config/app.php";
fingerprint(Celikom\Database\Connection::open($c),"api");
' "$app"
mapfile -t boots < <(find /srv/celikom-site -maxdepth 5 -type f -path '*/app/bootstrap.php')
[[ "${#boots[@]}" == 1 ]]
siteboot="${boots[0]}"
runuser -u celikom-site -- php -r '

function fingerprint(PDO $p, string $kind): void {
 $p->setAttribute(PDO::ATTR_STRINGIFY_FETCHES,true);
 $tables=$p->query("SHOW FULL TABLES WHERE Table_type=\"BASE TABLE\"")->fetchAll(PDO::FETCH_COLUMN);
 sort($tables,SORT_STRING);
 foreach($tables as $t){
  if(!preg_match("/^[a-zA-Z0-9_]+$/D",$t))throw new RuntimeException("Unexpected table");
  $q=$p->query("SELECT * FROM `".$t."`");
  $rows=[];
  while(($row=$q->fetch(PDO::FETCH_NUM))!==false){
   $h=hash_init("sha256");
   foreach($row as $v){
    if($v===null)hash_update($h,"N;");
    else {$v=(string)$v;hash_update($h,"V".strlen($v).":".$v);}
   }
   $rows[]=hash_final($h);
  }
  sort($rows,SORT_STRING);
  echo "FINGERPRINT ",$kind," ",$t," ",count($rows)," ",hash("sha256",implode("\n",$rows)),PHP_EOL;
 }
}

require $argv[1];$c=Celikom\Website\CmsConfig::databaseSettings();
fingerprint(Celikom\Website\Database::connect($c),"cms");
' "$siteboot"
audio=/srv/celikom/data/candidate-20261124/audio
media=$(runuser -u celikom-site -- php -r 'require $argv[1];$m=getenv("CELIKOM_SITE_MEDIA_DIR");if(!is_string($m)||!is_dir($m))exit(2);echo realpath($m);' "$siteboot")
[[ "$media" == /srv/celikom-site/* && -d "$audio" ]]
file_fingerprint(){
  cd "$1"
  find . -type f -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum | sha256sum | awk -v kind="$2" '{print "FILE_FINGERPRINT",kind,$1}'
}
(file_fingerprint "$audio" audio)
(file_fingerprint "$media" cms-media)
echo TARGET_SITE_BOOTSTRAP "$siteboot"
echo TARGET_MEDIA_DIR "$media"
docker ps --format '{{.Names}} {{.Image}}'
echo CELIKOM_TARGET_FINGERPRINT_OK
