<?php
declare(strict_types=1);
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli') exit(2);
try {
  $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
  $release=realpath($root.'/current');
  if (!$release || !is_link($root.'/current') || !str_starts_with($release,$root.'/releases/'))
     throw new RuntimeException('release');
  require $release.'/bootstrap.php';
  $config=require $release.'/config/app.php';
  if (!$config['owner_uploads_enabled'] || strlen($config['owner_upload_token'])<40 ||
      $config['db_name'] !== 'u235811320_celikom') throw new RuntimeException('owner_gate');
  $app=new Celikom\Application($config);
  $response=$app->handle('GET','/api/v1/tracks/upload-status',
     ['service'=>'yandex','track_id'=>'38436680']);
  if ($response->status !== 200 || (json_decode($response->body,true)['status']??null)!=='pending')
     throw new RuntimeException('pending_status');
  if ($app->handle('POST','/api/v1/uploads')->status!==401)
     throw new RuntimeException('no_auth_access');
  $pdo=Celikom\Database\Connection::open($config);
  $q=$pdo->query("SELECT r.status,r.is_active,a.sha256,a.storage_key FROM track_replacements r
      JOIN audio_assets a ON a.id=r.audio_asset_id WHERE r.id=1")->fetch(PDO::FETCH_ASSOC);
  if (!$q || $q['status']!=='approved' || (int)$q['is_active']!==1 ||
      !hash_equals($q['sha256'],hash_file('sha256',$root.'/shared/audio/'.$q['storage_key'])))
      throw new RuntimeException('approved_track_integrity');
  echo "Stage 7 hotfix live verification PASS: owner gate preserved; uploaded Track 38436680 pending; approved audio intact.\n";
} catch (Throwable) {
  fwrite(STDERR,"Stage 7 hotfix check failed.\n");
  exit(1);
}
