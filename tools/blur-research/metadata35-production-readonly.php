<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$ids=['22436','110374527','129803817','136272297','136404135','138629224','139871647','142464338','142977153','144713884','149870633','150160800','150770314','150838961','150838963','150838965','150838966','150838967','150838969','150838970','150838971','150838976','151055383','151055386','151055388','151055418','151055422','151055432','151055438','151055441','151055445','151855585','152396542','155025088','155095252'];
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$pdo=null;
try{
 $rel=realpath($base.'/current');
 if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))throw new RuntimeException('unsafe_release');
 require_once $rel.'/bootstrap.php';
 $cfg=require $rel.'/config/app.php';
 if(($cfg['environment']??'')!=='production')throw new RuntimeException('not_production');
 if(count($ids)!==35||count(array_unique($ids))!==35)throw new RuntimeException('invalid_ids');
 $pdo=\Celikom\Database\Connection::open($cfg);
 $pdo->exec('START TRANSACTION READ ONLY');
 $q=$pdo->prepare("SELECT r.id,r.status,r.is_active FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.id");
 $rows=[];$exists=0;
 foreach($ids as $id){
  $q->execute([$id]);$found=$q->fetchAll(PDO::FETCH_ASSOC);
  if(count($found))$exists++;
  $rows[]=['track_id'=>$id,'exists'=>count($found)>0,'versions'=>array_map(fn($v)=>['rid'=>$v['id']!==null?(int)$v['id']:null,'status'=>$v['status'],'active'=>(int)($v['is_active']??0)],$found)];
 }
 $pdo->rollBack();
 echo json_encode(['status'=>'METADATA35_PRODUCTION_READONLY','checked'=>count($rows),'existing'=>$exists,'absent'=>count($rows)-$exists,'writes'=>0,'records'=>$rows],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $e){
 if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
 fwrite(STDERR,'METADATA35_READONLY_FAILED: '.$e->getMessage()."\n");exit(2);
}
