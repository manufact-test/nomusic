<?php
declare(strict_types=1);

/** Read-only independent live verification of exactly 50 selected pending records. */
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';$stage=__DIR__;
try{
    if(!preg_match('~^'.preg_quote($base,'~').'/incoming/blur-fifty-[0-9]{8,16}$~D',$stage)
       || is_link($stage)||realpath($stage)!==$stage)throw new RuntimeException('unsafe_path');
    $rel=realpath($base.'/current');
    if(!$rel || !is_link($base.'/current') || !str_starts_with($rel,$base.'/releases/'))
        throw new RuntimeException('unsafe_release');
    require_once $rel.'/bootstrap.php';
    $cfg=require $rel.'/config/app.php';
    $pdo=\Celikom\Database\Connection::open($cfg);
    $entries=json_decode(file_get_contents($stage.'/selected.json'),true,512,JSON_THROW_ON_ERROR)['selected']??null;
    if(!is_array($entries)||count($entries)!==50)throw new RuntimeException('invalid_verification_list');
    $pdo->exec('START TRANSACTION READ ONLY');
    $find=$pdo->prepare("SELECT r.id,r.status,r.is_active,a.sha256,a.size_bytes,
         (SELECT COUNT(*) FROM track_replacements other WHERE other.track_id=t.id) AS total_versions
         FROM tracks t JOIN track_replacements r ON r.track_id=t.id
         JOIN audio_assets a ON a.id=r.audio_asset_id
         WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.id DESC LIMIT 1");
    $ok=[];$missing=[];
    foreach($entries as $e){
        $find->execute([$e['id']]);$r=$find->fetch(PDO::FETCH_ASSOC);
        if($r && $r['status']==='pending'&&(int)$r['is_active']===0
          && (int)$r['size_bytes']===(int)$e['size'] && (int)$r['total_versions']===1) {
            $ok[]=['track_id'=>$e['id'],'replacement_id'=>(int)$r['id']];
        } else $missing[]=$e['id'];
    }
    $pdo->rollBack();
    if(count($ok)!==50||$missing)throw new RuntimeException('not_exactly_50_pending:'.implode(',',$missing));
    echo json_encode(['status'=>'LIVE_VERIFIED','pending_count'=>count($ok),
        'rights_confirmed'=>false,'active'=>0,'records'=>$ok,'writes'=>0],
        JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
}catch(Throwable $error){
    if(isset($pdo)&&$pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,'LIVE_VERIFY_REFUSED: '.$error->getMessage()."\n");exit(1);
}
