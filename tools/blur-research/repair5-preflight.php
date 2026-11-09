<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$source=<<<'JSON'
[{"id":"39580348","artist":"Овсянкин feat. Вертушка Газманова","title":"Тебя прёт габба","sha256":"0000000000000000000000000000000000000000000000000000000000000000"},{"id":"136404135","artist":"ПОШЛАЯ МОЛЛИ","title":"Школа Не Нужна","sha256":"0000000000000000000000000000000000000000000000000000000000000000"},{"id":"144998587","artist":"NEXTIME","title":"СВЕТЛАНА!","sha256":"0000000000000000000000000000000000000000000000000000000000000000"},{"id":"145242788","artist":"паранойя","title":"ALASKA PUFFER 2","sha256":"0000000000000000000000000000000000000000000000000000000000000000"},{"id":"146150936","artist":"NEXTIME","title":"АНТИСВЕТЛАНА","sha256":"0000000000000000000000000000000000000000000000000000000000000000"}]
JSON;
$rows=json_decode($source,true,512,JSON_THROW_ON_ERROR);
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';$pdo=null;
try {
 $rel=realpath($base.'/current');
 if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))throw new RuntimeException('unsafe_release');
 require_once $rel.'/bootstrap.php';$cfg=require $rel.'/config/app.php';
 if(($cfg['environment']??'')!=='production'||count($rows)!==5)throw new RuntimeException('bad_environment_or_list');
 $pdo=\Celikom\Database\Connection::open($cfg);$pdo->exec('START TRANSACTION READ ONLY');
 $idQ=$pdo->prepare("SELECT id FROM tracks WHERE service='yandex' AND service_track_id=? LIMIT 1");
 $nameQ=$pdo->prepare("SELECT service_track_id FROM tracks WHERE service='yandex' AND LOWER(TRIM(artist))=LOWER(TRIM(?)) AND LOWER(TRIM(title))=LOWER(TRIM(?)) LIMIT 5");
 $requestQ=$pdo->prepare("SELECT COUNT(*) FROM track_requests WHERE service='yandex' AND service_track_id=?");
 $tombQ=$pdo->prepare("SELECT COUNT(*) FROM bulk_moderation_tombstones WHERE service='yandex' AND service_track_id=?");
 $assetQ=$pdo->prepare("SELECT COUNT(*) FROM audio_assets WHERE sha256=?");
 $out=[];
 foreach($rows as $x){
  $idQ->execute([$x['id']]);$foundId=$idQ->fetchColumn()!==false;
  $nameQ->execute([$x['artist'],$x['title']]);$same=$nameQ->fetchAll(PDO::FETCH_COLUMN);
  $requestQ->execute([$x['id']]);$req=(int)$requestQ->fetchColumn();
  $tombQ->execute([$x['id']]);$tomb=(int)$tombQ->fetchColumn();
  $assetQ->execute([$x['sha256']]);$asset=(int)$assetQ->fetchColumn();
  $out[]=['id'=>$x['id'],'id_exists'=>$foundId,'same_title_ids'=>$same,'request_count'=>$req,'tombstone_count'=>$tomb,'asset_dupe_count'=>$asset,
          'eligible'=>!$foundId&&!$same&&!$req&&!$tomb&&!$asset];
 }
 $pdo->rollBack();
 echo json_encode(['status'=>'REPAIR5_PREFLIGHT_READONLY','checked'=>count($out),'eligible'=>count(array_filter($out,fn($x)=>$x['eligible'])),'writes'=>0,'rows'=>$out],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $e){if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();fwrite(STDERR,'REFUSED '.$e->getMessage()."\n");exit(2);}
