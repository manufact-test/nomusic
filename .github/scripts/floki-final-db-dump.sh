#!/bin/bash
set -Eeuo pipefail
umask 077
PHP=/opt/alt/php83/usr/bin/php
"$PHP" -r '
$kind=$argv[1];
if($kind==="api"){
 $base="/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/current";
 require $base."/bootstrap.php"; $c=require $base."/config/app.php";
 $host=$c["db_host"]; $port=$c["db_port"]; $db=$c["db_name"]; $user=$c["db_user"]; $password=$c["db_password"];
 if($db!=="u235811320_celikom")exit(2);
}elseif($kind==="cms"){
 require "/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com/celikom-private/app/bootstrap.php";
 $c=Celikom\Website\CmsConfig::databaseSettings();
 $host=$c["host"]; $port=3306; $db=$c["dbname"]; $user=$c["user"]; $password=$c["password"];
 if(!preg_match("/^u235811320_celikom_stage[a-zA-Z0-9_]*$/D",$db))exit(2);
}else exit(2);
putenv("MYSQL_PWD=".$password);
$cmd="mysqldump --single-transaction --quick --no-tablespaces --skip-lock-tables --hex-blob --triggers --host=".escapeshellarg($host)." --port=".escapeshellarg((string)$port)." --user=".escapeshellarg($user)." ".escapeshellarg($db);
passthru($cmd,$rc); exit($rc);
' "$1" | gzip -1
