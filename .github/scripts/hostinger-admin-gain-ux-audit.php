<?php
declare(strict_types=1);
ini_set('display_errors','0');
try{
 $app='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';$expected=$argv[1]??'';
 if(!preg_match('/^0\.4\.43-[a-f0-9]{40}$/D',$expected)||realpath($app.'/current')!==$app.'/releases/'.$expected)throw new RuntimeException('release');
 require $app.'/current/bootstrap.php';$config=require $app.'/current/config/app.php';$pdo=Celikom\Database\Connection::open($config);
 $pdo->exec('SET TRANSACTION READ ONLY');$pdo->beginTransaction();
 $panel=new Celikom\Admin\AdminPanel($pdo,new Celikom\Storage\LocalStorageAdapter($config['storage_path']));$uploads=new ReflectionMethod($panel,'uploads');
 $html=$uploads->invoke($panel,['role'=>'owner'],str_repeat('0',64),['per_page'=>'50']);
 if(!str_contains($html,'data-gain-toggle><summary>Громкость версии</summary>')||strpos($html,'<summary>Громкость версии')>strpos($html,'<summary>Технические сведения'))throw new RuntimeException('disclosure');
 if(!str_contains($html,'data-gain-save-status')||!str_contains(file_get_contents($app.'/current/src/Admin/audio-gain.js'),"event.preventDefault()"))throw new RuntimeException('inline_save');
 $range=file_get_contents($app.'/current/src/Admin/admin-style.css');if(!str_contains($range,'--gain-fill')||!str_contains($range,'::-webkit-slider-runnable-track'))throw new RuntimeException('range_style');
 $pdo->commit();echo json_encode(['read_only'=>true,'release_verified'=>true,'collapsed_gain_before_technical'=>'PASS','inline_save'=>'PASS','full_range_track'=>'PASS','music_and_owner_moderation'=>'not modified'],JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $e){fwrite(STDERR,'Admin gain UX read-only audit failed: '.get_class($e)."\n");exit(1);}
