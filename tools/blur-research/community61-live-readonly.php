<?php
declare(strict_types=1);
/** Independent SELECT-only probe of new public YM Liberty IDs; no audio downloads, no writes. */
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$ids=["126242685","109584282","148716112","148716136","90841995","109584286","148716975","70155207","132017316","48591477","148716095","50534126","105785654","148717008","40498614","149649674","149649675","149649684","64002994","36772429","116515816","45551590","77226183","154309285","62804776","48591492","143073648","145746152","141103777","106778345","148085480","70796267","154295526","105569668","60441901","151387883","10705201","45239752","137121455","77684870","59735933","114023363","56988263","154252085","108681481","94970834","146534025","107650349","142931494","153622672","27317247","133294493","147713024","108892488","138786935","93453301","117144301","93453297","118111186","93453294","153367808"];
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$pdo=null;
try {
    $rel=realpath($base.'/current');
    if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))throw new RuntimeException('unsafe_release');
    require_once $rel.'/bootstrap.php';
    $cfg=require $rel.'/config/app.php';
    if(($cfg['environment']??'')!=='production')throw new RuntimeException('not_production');
    if(count($ids)!==61||count(array_unique($ids))!==61)throw new RuntimeException('candidate_ids_invalid');
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
    echo json_encode(['status'=>'YM_LIBERTY_COMMUNITY_REPORTS_61_READ_ONLY','checked'=>count($ids),'existing_tracks'=>$existing,'absent_tracks'=>$absent,'requests'=>$requests,'tombstones'=>$tombstones,'writes'=>0,'records'=>$rows],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $e){
    if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,'YM_COMMUNITY61_READONLY_REFUSED: '.$e->getMessage()."\n");exit(2);
}
