<?php
declare(strict_types=1);
ini_set('display_errors','0');
try {
 $app='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
 $expected=$argv[1]??'';
 if(!preg_match('/^0\.4\.42-[a-f0-9]{40}$/D',$expected))throw new RuntimeException('release_argument');
 $release=realpath($app.'/current');
 if($release!==$app.'/releases/'.$expected)throw new RuntimeException('release');
 require $release.'/bootstrap.php';$config=require $release.'/config/app.php';
 $pdo=Celikom\Database\Connection::open($config);$pdo->exec('SET TRANSACTION READ ONLY');$pdo->beginTransaction();
 $q=$pdo->prepare('SELECT sha256 FROM schema_migrations WHERE version=?');$q->execute(['017_song_support.sql']);
 if(!hash_equals(hash_file('sha256',$release.'/migrations/017_song_support.sql'),(string)$q->fetchColumn()))throw new RuntimeException('migration');
 $counts=$pdo->query("SELECT COUNT(*) AS total,SUM(kind='general') AS ordinary,SUM(kind='song') AS songs FROM support_tickets")->fetch(PDO::FETCH_ASSOC);
 $account=(int)$pdo->query('SELECT user_id FROM support_tickets ORDER BY id LIMIT 1')->fetchColumn();
 if($account>0){
  $view=new Celikom\Support\SupportAdminView($pdo);
  foreach(['general','song'] as $kind){$html=$view->render(str_repeat('0',64),0,1,1,$account,$kind);if(!str_contains($html,'Обычные обращения')||!str_contains($html,'Проблемы с песнями'))throw new RuntimeException('support_sections');}
 }
 $panel=new Celikom\Admin\AdminPanel($pdo,new Celikom\Storage\LocalStorageAdapter($config['storage_path']));
 $requests=new ReflectionMethod($panel,'requests');$html=$requests->invoke($panel,['role'=>'viewer'],str_repeat('0',64),['per_page'=>'50']);
 if(!str_contains($html,'Чем больше уникальных пользователей'))throw new RuntimeException('queue_copy');
 preg_match_all('/Track ID ([0-9]+)/',$html,$matches);if(count($matches[1])!==count(array_unique($matches[1])))throw new RuntimeException('duplicate_cards');
 preg_match_all('/Уникальных предложений: ([0-9]+)/',$html,$matches);$demand=array_map('intval',$matches[1]);$sorted=$demand;rsort($sorted);if($demand!==$sorted)throw new RuntimeException('popularity_order');
 $normalized=Celikom\Support\SongReport::normalize(['category'=>'audio_issue','track'=>['id'=>'50163040','title'=>'Read-only fixture','access_token'=>'excluded'],'version'=>'0.4.42','diagnostics'=>['phase'=>'READY','token'=>'excluded','network'=>[]]]);
 if(str_contains(json_encode($normalized),'excluded'))throw new RuntimeException('privacy');
 foreach(['50163040','48591588'] as $id){$q=$pdo->prepare("SELECT a.duration_ms,t.duration_ms AS original_ms,r.version FROM tracks t JOIN track_replacements r ON r.track_id=t.id JOIN audio_assets a ON a.id=r.audio_asset_id WHERE t.service='yandex' AND t.service_track_id=? AND r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL");$q->execute([$id]);$fixed=$q->fetch(PDO::FETCH_ASSOC);if(!$fixed||abs((int)$fixed['duration_ms']-(int)$fixed['original_ms'])>1500||(int)$fixed['version']!==3)throw new RuntimeException('repaired_audio');}
 $pdo->commit();
 echo json_encode(['read_only'=>true,'release_verified'=>true,'migration_verified'=>true,'support_category_ui'=>'PASS','ordinary_tickets'=>(int)$counts['ordinary'],'song_tickets'=>(int)$counts['songs'],'request_grouping_and_order'=>'PASS','diagnostic_whitelist'=>'PASS','two_repaired_audio_versions'=>'preserved'],JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $e){fwrite(STDERR,'Feedback read-only audit failed: '.get_class($e)."\n");exit(1);}
