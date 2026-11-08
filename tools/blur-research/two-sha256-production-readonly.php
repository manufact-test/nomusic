<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$hashes=[
'4ae0d6d6c857a8112b037ea740cd30ebdc9789b991ea13b655287edebcc2cefa',
'bd4aa3081fd914cf577dfd2c9b6d38a0798391cf9ec9acd549775cf6287ad5e2'
];
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$pdo=null;
try{
 $rel=realpath($base.'/current');
 if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))throw new RuntimeException('unsafe_release');
 require_once $rel.'/bootstrap.php';
 $cfg=require $rel.'/config/app.php';
 if(($cfg['environment']??'')!=='production')throw new RuntimeException('not_production');
 $pdo=\Celikom\Database\Connection::open($cfg);
 $pdo->exec('START TRANSACTION READ ONLY');
 $q=$pdo->prepare("SELECT id,sha256 FROM audio_assets WHERE sha256=?");
 $records=[];
 foreach($hashes as $h){
  $q->execute([$h]);$found=$q->fetchAll(PDO::FETCH_ASSOC);
  $records[]=['sha256'=>$h,'existing_assets'=>count($found)];
 }
 $pdo->rollBack();
 echo json_encode(['status'=>'TWO_SHA256_PRODUCTION_READONLY','checked'=>2,'writes'=>0,'records'=>$records],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $e){
 if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
 fwrite(STDERR,'TWO_SHA256_REFUSED: '.$e->getMessage()."\n");exit(2);
}
