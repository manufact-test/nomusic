<?php
declare(strict_types=1);
// Disposable database fixture ONLY. Synthetic 4-second sine wave, no music.
require dirname(__DIR__).'/bootstrap.php';

use Celikom\Application\Mp3Inspector;
use Celikom\Database\Connection;
use Celikom\Storage\LocalStorageAdapter;

$source=$argv[1]??'';$render=$argv[2]??'';
if (!is_file($source) || !is_file($render)) exit(2);
$config=require dirname(__DIR__).'/config/app.php';
if (($config['environment']??'')!=='test') exit(2);
$pdo=Connection::open($config);
$storage=new LocalStorageAdapter($config['storage_path']);
$sha=hash_file('sha256',$source);
$renderSha=hash_file('sha256',$render);
$duration=(new Mp3Inspector())->durationMs($source);
$renderDuration=(new Mp3Inspector())->durationMs($render);
if (!is_string($sha)||!is_string($renderSha)||!is_int($duration)||
    !is_int($renderDuration)||abs($renderDuration-$duration)>1500) exit(2);
$key='audio/'.substr($sha,0,2).'/'.$sha.'.mp3';
$stream=fopen($source,'rb');$storage->put($key,$stream);fclose($stream);
$track=$pdo->prepare("INSERT INTO tracks (service,service_track_id,title,artist,duration_ms)
 VALUES('yandex','40371622','synthetic gain test','ci',?)");
$track->execute([$duration]);
$trackId=(int)$pdo->lastInsertId();
$asset=$pdo->prepare("INSERT INTO audio_assets (storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms)
 VALUES ('local',? ,? ,'audio/mpeg',?,?)");
$asset->execute([$key,$sha,filesize($source),$duration]);
$assetId=(int)$pdo->lastInsertId();
$replace=$pdo->prepare("INSERT INTO track_replacements (track_id,audio_asset_id,status,is_active,version,gain_db)
 VALUES(?,?,'approved',1,1,11.5)");
$replace->execute([$trackId,$assetId]);
$id=(int)$pdo->lastInsertId();
if($id<1)exit(2);
echo implode(' ',[$id,$sha,'1','11.5',$renderSha]),"\n";
