<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$ids=['138629224','129803817','111001121','110374527','112132165','149870633','136272297','39193875','36045842','39580298','34972342','37231301','37231311','39580348','44803091','59397779','71650516','70748121','36360202','36620592','58746554','130751224','119351895','132217704','27737513','155025088','152396542','126984723','136404135'];
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$pdo=null;
try{
 $rel=realpath($base.'/current');
 if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))throw new RuntimeException('unsafe_release');
 require_once $rel.'/bootstrap.php';
 $cfg=require $rel.'/config/app.php';
 if(($cfg['environment']??'')!=='production')throw new RuntimeException('not_production');
 if(count($ids)!==29||count(array_unique($ids))!==29)throw new RuntimeException('invalid_ids');
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
 echo json_encode(['status'=>'STORAGE29_PRODUCTION_READONLY','checked'=>count($rows),'existing'=>$exists,'absent'=>count($rows)-$exists,'writes'=>0,'records'=>$rows],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $e){
 if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
 fwrite(STDERR,'STORAGE29_READONLY_FAILED: '.$e->getMessage()."\n");exit(2);
}
