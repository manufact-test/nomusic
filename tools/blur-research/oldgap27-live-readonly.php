<?php
declare(strict_types=1);
/** Independent SELECT-only probe of new public YM Liberty IDs; no audio downloads, no writes. */
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$ids=["101389541","103080185","109051383","109332240","112132165","125243454","125714579","126054904","132720741","148715960","148716091","148716101","148716132","148716140","148716901","148716938","148717002","148825093","149665384","36063264","38559822","40498609","40498611","41570482","50400505","57340475","81874002"];
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$pdo=null;
try {
    $rel=realpath($base.'/current');
    if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))throw new RuntimeException('unsafe_release');
    require_once $rel.'/bootstrap.php';
    $cfg=require $rel.'/config/app.php';
    if(($cfg['environment']??'')!=='production')throw new RuntimeException('not_production');
    if(count($ids)!==27||count(array_unique($ids))!==27)throw new RuntimeException('candidate_ids_invalid');
    $pdo=\Celikom\Database\Connection::open($cfg);
    $pdo->exec('START TRANSACTION READ ONLY');
    $q=$pdo->prepare("SELECT r.id,r.status,r.is_active FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.id");
    $req=$pdo->prepare("SELECT COUNT(*) FROM track_requests WHERE service='yandex' AND service_track_id=?");
    $tomb=$pdo->prepare("SELECT COUNT(*) FROM bulk_moderation_tombstones WHERE service='yandex' AND service_track_id=?");
    $rows=[];$existing=0;$absent=0;$requests=0;$tombstones=0;
    foreach($ids as $id){
        $q->execute([$id]);$found=$q->fetchAll(PDO::FETCH_ASSOC);
        $req->execute([$id]);$request=(int)$req->fetchColumn();
        $tomb->execute([$id]);$deleted=(int)$tomb->fetchColumn();
        $exists=(count($found)>0);if($exists)$existing++;else $absent++;
        if($request)$requests++;if($deleted)$tombstones++;
        $rows[]=['id'=>$id,'exists'=>$exists,'versions'=>array_map(fn($v)=>['rid'=>$v['id']!==null?(int)$v['id']:null,'status'=>$v['status'],'active'=>(int)($v['is_active']??0)],$found),'request'=>$request>0,'tombstone'=>$deleted>0];
    }
    $pdo->rollBack();
    echo json_encode(['status'=>'OLDER_SOURCE_GAPS_27_READ_ONLY','checked'=>count($ids),'existing_tracks'=>$existing,'absent_tracks'=>$absent,'requests'=>$requests,'tombstones'=>$tombstones,'writes'=>0,'records'=>$rows],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $e){
    if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,'OLDGAP27_READONLY_REFUSED: '.$e->getMessage()."\n");exit(2);
}
