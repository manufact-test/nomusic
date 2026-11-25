#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only runtime identity and public acceptance gate check.
# No restore, database mutation, grant change, service reload or source freeze.
app=/srv/celikom/app/staging-20261122
runuser -u www-data -- php -r '
require $argv[1]."/bootstrap.php";
$c=require $argv[1]."/config/app.php";
$p=Celikom\Database\Connection::open($c);
$target="celikom_cutover_20261124";
$q=$p->prepare("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=?");
$q->execute([$target]);
printf("API_RUNTIME_CONNECTED=1\nAPI_CANDIDATE_VISIBLE_TO_RUNTIME=%d\n",(int)$q->fetchColumn());
$q=$p->prepare("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=? AND TABLE_TYPE=?");
$q->execute([$target,"BASE TABLE"]);
printf("API_CANDIDATE_VISIBLE_TABLE_COUNT=%d\n",(int)$q->fetchColumn());
$grants=$p->query("SHOW GRANTS")->fetchAll(PDO::FETCH_COLUMN);
$exact=0;
foreach($grants as $line){
 if(strpos($line,"ON \x60celikom\\_cutover\\_20261124\x60.*")===false) continue;
 $priv=substr($line,0,strpos($line," ON "));
 $all=true;foreach(["SELECT","INSERT","UPDATE","DELETE"] as $v){if(!preg_match("/\b".$v."\b/",$priv))$all=false;}
 if($all)$exact=1;
}
printf("API_RUNTIME_SHOW_GRANTS_EXACT_CRUD=%d\n",$exact);
' "$app"
mysql --protocol=socket -uroot --batch --skip-column-names -e "SELECT CONCAT('CMS_CANDIDATE_EXISTS=',COUNT(*)) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='celikom_website_cutover_20261124'"
systemctl is-active nginx php8.3-fpm celikom-ci-runner.service forgejo celikom-mirror-sync.timer
for item in 'api.celikom.com /api/v1/health 200' 'api.celikom.com /api/v1/config 200' 'api.celikom.com /admin/ 404' 'celikom.com / 401' 'celikom.com /admin/ 401' 'celikom.com /downloads/windows/CELIKOM-Windows-0.24.55.exe 401' 'celikom.com /downloads/extension/celikom-extension-0.4.73.zip 401' 'celikom.com /updates/android/stable.json 401'; do
  read -r host route expected <<< "$item"
  code=$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' "https://$host$route")
  printf 'ROUTE %s%s %s\n' "$host" "$route" "$code"
  [[ "$code" == "$expected" ]]
done
echo CELIKOM_RUNTIME_READONLY_GATE_CHECK_COMPLETE
