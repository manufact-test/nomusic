<?php
declare(strict_types=1);
/** Independent, read-only live audit of an exact 50/200 pinned pending list.
 * Checks DB state, private bytes, SHA-256, MIME, version uniqueness, catalogue absence.
 * Never updates database, permissions or rights.
 */
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$stage=__DIR__;
$pdo=null;
try {
    if(is_link($stage)||!preg_match('~^'.preg_quote($base,'~').'/incoming/blur-fifty-[0-9]{8,16}$~D',$stage)
       || realpath($stage)!==$stage)throw new RuntimeException('unsafe_staging');
    $rel=realpath($base.'/current');
    if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))
        throw new RuntimeException('unsafe_current_release');
    require_once $rel.'/bootstrap.php';
    $cfg=require $rel.'/config/app.php';
    if(($cfg['environment']??'')!=='production'||($cfg['storage_driver']??'')!=='local'
       ||realpath((string)$cfg['storage_path'])!==$base.'/shared/audio')
        throw new RuntimeException('unexpected_production_storage');
    $plan=json_decode(file_get_contents($stage.'/selected.json'),true,512,JSON_THROW_ON_ERROR);
    $expected=$plan['selected']??null;
    $n=is_array($expected)?count($expected):0;
    if(($n<1 || $n>200)||($plan['target_pending']??null)!==$n
       ||($plan['source_commit']??'')!=='multisource-20261109')
        throw new RuntimeException('unexpected_fixed_list');
    $pdo=\Celikom\Database\Connection::open($cfg);
    $store=new \Celikom\Storage\LocalStorageAdapter($cfg['storage_path']);
    $catalogue=(new \Celikom\Application\ReplacementCatalogueService($pdo))->snapshot();
    $listed=[];
    foreach(($catalogue['tracks']??[]) as $item)$listed[(string)$item['track_id']]=true;
    $q=$pdo->prepare("SELECT r.id,r.status,r.is_active,r.approved_at,r.approved_by_admin_id,r.disabled_at,
      a.storage_driver,a.storage_key,a.sha256,a.size_bytes,a.mime_type,a.duration_ms
      FROM tracks t JOIN track_replacements r ON r.track_id=t.id
      JOIN audio_assets a ON a.id=r.audio_asset_id
      WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.id");
    $issues=[];$rows=[];$bytes=0;$verified=0;$seen=[];
    $pdo->exec('START TRANSACTION READ ONLY');
    foreach($expected as $e) {
        $id=$e['id']??'';
        if(!is_string($id)||!preg_match('/^[1-9][0-9]{0,19}$/D',$id)||isset($seen[$id]))
            throw new RuntimeException('invalid_or_repeated_id');
        $seen[$id]=true;
        $q->execute([$id]);$found=$q->fetchAll(PDO::FETCH_ASSOC);
        if(count($found)!==1){$issues[]=['id'=>$id,'error'=>'missing_or_multiple_replacements'];continue;}
        $r=$found[0];
        if($r['status']!=='pending'||(int)$r['is_active']!==0||$r['approved_at']!==null
           ||$r['approved_by_admin_id']!==null||$r['disabled_at']!==null){
            $issues[]=['id'=>$id,'error'=>'not_unapproved_pending'];continue;
        }
        if(isset($listed[$id])){
            $issues[]=['id'=>$id,'error'=>'pending_in_active_catalogue'];continue;
        }
        if($r['storage_driver']!=='local'||$r['mime_type']!=='audio/mpeg'
           ||(int)$r['size_bytes']!==(int)($e['size']??-1)
           ||abs((int)$r['duration_ms']-(int)($e['duration_ms']??-1))>1500
           ||!preg_match('~^audio/[a-f0-9]{2}/[a-f0-9]{64}\\.mp3$~D',(string)$r['storage_key'])
           ||!$store->exists((string)$r['storage_key'])
           ||$store->getSize((string)$r['storage_key'])!==(int)$r['size_bytes']
           ||$store->getMimeType((string)$r['storage_key'])!=='audio/mpeg'){
            $issues[]=['id'=>$id,'error'=>'private_audio_storage_mismatch'];continue;
        }
        $stream=$store->openStream((string)$r['storage_key']);
        try{$h=hash_init('sha256');hash_update_stream($h,$stream);}
        finally{fclose($stream);}
        if(!hash_equals((string)$r['sha256'],hash_final($h))){
            $issues[]=['id'=>$id,'error'=>'private_audio_digest_mismatch'];continue;
        }
        $verified++;$bytes+=(int)$r['size_bytes'];
        $rows[]=['track_id'=>$id,'replacement_id'=>(int)$r['id']];
    }
    $pdo->rollBack();
    $out=['status'=>'LIVE'.$n.'_PENDING_VERIFIED',
          'checked'=>$n,'pending_count'=>$verified,'files_verified'=>$verified,
          'bytes_verified'=>$bytes,'automatic_approvals'=>0,'active'=>0,
          'rights_confirmed_by_import'=>false,'writes'=>0,'issues'=>$issues,'records'=>$rows,
          'pass'=>$verified===$n && count($seen)===$n && !$issues];
    echo json_encode($out,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
    if(!$out['pass'])exit(1);
}catch(Throwable $e){
    if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,'LIVE_PENDING200_AUDIT_REFUSED: '.$e->getMessage()."\n");
    exit(2);
}
