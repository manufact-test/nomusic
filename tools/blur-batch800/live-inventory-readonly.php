<?php
declare(strict_types=1);
// Strict read-only production inventory after owner-authorised 4x50 import. No user data.
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$pdo=null;
try{
  $rel=realpath($base.'/current');
  if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))throw new RuntimeException('unsafe_current_release');
  require_once $rel.'/bootstrap.php';
  $cfg=require $rel.'/config/app.php';
  if(($cfg['environment']??'')!=='production'||($cfg['storage_driver']??'')!=='local')throw new RuntimeException('not_production_local_storage');
  $pdo=\Celikom\Database\Connection::open($cfg);
  $pdo->exec('START TRANSACTION READ ONLY');
  $rows=$pdo->query('SELECT status,is_active,COUNT(*) AS n FROM track_replacements GROUP BY status,is_active')->fetchAll(PDO::FETCH_ASSOC);
  $byStatus=[];$replacementCount=0;
  foreach($rows as $r){$key=(string)$r['status'].':'.(int)$r['is_active'];$byStatus[$key]=(int)$r['n'];$replacementCount+=(int)$r['n'];}
  $a=$pdo->query("SELECT COUNT(*) AS n, COALESCE(SUM(size_bytes),0) AS bytes, COUNT(DISTINCT storage_key) AS distinct_storage_keys FROM audio_assets WHERE storage_driver='local'")->fetch(PDO::FETCH_ASSOC);
  $tracks=(int)$pdo->query("SELECT COUNT(*) FROM tracks WHERE service='yandex'")->fetchColumn();
  $req=(int)$pdo->query("SELECT COUNT(*) FROM track_requests WHERE service='yandex'")->fetchColumn();
  $tomb=(int)$pdo->query("SELECT COUNT(*) FROM bulk_moderation_tombstones WHERE service='yandex'")->fetchColumn();
  $pdo->rollBack();
  $catalogue=(new \Celikom\Application\ReplacementCatalogueService($pdo))->snapshot();
  echo json_encode(['status'=>'LIVE_LIBRARY_INVENTORY_READ_ONLY','yandex_tracks'=>$tracks,
     'replacement_versions_total'=>$replacementCount,'replacement_statuses'=>$byStatus,
     'catalogue_active'=>(int)$catalogue['total_tracks'],'private_audio_assets'=>(int)$a['n'],
     'distinct_storage_keys'=>(int)$a['distinct_storage_keys'],'private_audio_bytes'=>(int)$a['bytes'],
     'open_yandex_requests'=>$req,'yandex_tombstones'=>$tomb,'writes'=>0],
     JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $error){
 if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
 fwrite(STDERR,'LIVE_INVENTORY_REFUSED: '.$error->getMessage()."\n");exit(2);
}
