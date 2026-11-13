<?php
declare(strict_types=1);
ini_set('display_errors','0');
if (PHP_SAPI !== 'cli') exit(2);
try {
  $site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
  $root=$site.'/celikom';
  $release=realpath($root.'/current');
  if (!$release || !is_link($root.'/current') || !str_starts_with($release,$root.'/releases/')) throw new RuntimeException('release');
  require $release.'/bootstrap.php';
  $config=require $release.'/config/app.php';
  if ($config['db_name'] !== 'u235811320_celikom') throw new RuntimeException('db');
  $pdo=Celikom\Database\Connection::open($config);
  $stmt=$pdo->prepare("SELECT t.service_track_id, r.id replacement_id, r.status, r.is_active, a.sha256, a.size_bytes, a.duration_ms, a.storage_key, COUNT(u.id) submissions
       FROM tracks t JOIN track_replacements r ON r.track_id=t.id JOIN audio_assets a ON a.id=r.audio_asset_id
       LEFT JOIN upload_submissions u ON u.replacement_id=r.id
       WHERE t.service='yandex' AND t.service_track_id=?
       GROUP BY t.service_track_id,r.id,r.status,r.is_active,a.sha256,a.size_bytes,a.duration_ms,a.storage_key
       ORDER BY r.id");
  $stmt->execute(['38436680']);
  $matches=$stmt->fetchAll(PDO::FETCH_ASSOC);
  $items=[];
  foreach($matches as $record) {
    $path=$root.'/shared/audio/'.$record['storage_key'];
    if (!str_starts_with($record['storage_key'],'audio/') ||
        str_contains($record['storage_key'],'..')) throw new RuntimeException('audio_path');
    $ok=is_file($path) && (int)filesize($path)===(int)$record['size_bytes'] &&
      hash_equals($record['sha256'],hash_file('sha256',$path));
    $items[]=['track_id'=>$record['service_track_id'],'replacement_id'=>(int)$record['replacement_id'],
      'status'=>$record['status'],'active'=>(bool)$record['is_active'],
      'submissions'=>(int)$record['submissions'],'duration_ms'=>(int)$record['duration_ms'],
      'size_bytes'=>(int)$record['size_bytes'],'private_file_hash_valid'=>$ok];
  }
  $approved=$pdo->query("SELECT r.status,r.is_active,a.sha256,a.size_bytes,a.storage_key
     FROM track_replacements r JOIN audio_assets a ON a.id=r.audio_asset_id WHERE r.id=1")->fetch(PDO::FETCH_ASSOC);
  $approvedOk=$approved && $approved['status']==='approved' && (int)$approved['is_active']===1 &&
      is_file($root.'/shared/audio/'.$approved['storage_key']) &&
      hash_equals($approved['sha256'],hash_file('sha256',$root.'/shared/audio/'.$approved['storage_key']));
  $count=(int)$pdo->query("SELECT COUNT(*) FROM track_replacements WHERE status='pending' AND is_active=0")->fetchColumn();
  $recent=$pdo->query("SELECT t.service_track_id,r.id replacement_id,r.status,r.is_active,
        t.artist,t.title,r.created_at
      FROM track_replacements r JOIN tracks t ON t.id=r.track_id
      WHERE r.id<>1 AND t.service='yandex' ORDER BY r.id DESC LIMIT 8")->fetchAll(PDO::FETCH_ASSOC);
  echo json_encode(['recent_replacements'=>$recent,'lookup_track_id'=>'38436680','matches'=>$items,
    'all_pending_count'=>$count,'original_approved_audio_intact'=>$approvedOk,
    'owner_uploads_enabled'=>$config['owner_uploads_enabled']], JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES),"\n";
  if (!$approvedOk) exit(1);
} catch(Throwable) {fwrite(STDERR,"Stage 7 read-only audit failed.\n");exit(1);}
