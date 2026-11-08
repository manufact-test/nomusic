<?php
declare(strict_types=1);

/**
 * One user-approved 50-record batch into private pending moderation.
 * Every row is a separate durable transaction; retries reuse matching pending
 * mappings and never approve, activate or overwrite a different candidate.
 */
if (PHP_SAPI!=='cli' || count($argv)!==1) { fwrite(STDERR,"CLI_ONLY\n");exit(2); }
ini_set('display_errors','0');
error_reporting(E_ALL);
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$stage=__DIR__;
$pdo=null;$locked=false;$dry=getenv('CELIKOM_BLUR_DRY_RUN')==='1';
$new=[];$resumed=[];
try {
    if(is_link($stage) || !preg_match('~^'.preg_quote($base,'~').'/incoming/blur-fifty-[0-9]{8,16}$~D',$stage)
       || realpath($stage)!==$stage || !is_dir($stage)) throw new RuntimeException('unsafe_private_staging');
    $rel=realpath($base.'/current');
    if(!is_link($base.'/current') || !$rel || !str_starts_with($rel,$base.'/releases/')
       || !is_file($rel.'/bootstrap.php') || !is_file($rel.'/config/app.php'))
        throw new RuntimeException('unsafe_current_release');
    require_once $rel.'/bootstrap.php';
    $cfg=require $rel.'/config/app.php';
    if(($cfg['environment']??'')!=='production' || ($cfg['storage_driver']??'')!=='local'
       || realpath((string)$cfg['storage_path'])!==$base.'/shared/audio')
        throw new RuntimeException('unexpected_storage_environment');
    $manifest=json_decode(file_get_contents($stage.'/selected.json'),true,512,JSON_THROW_ON_ERROR);
    $entries=$manifest['selected']??null;
    if(!is_array($entries) || (count($entries)<1 || count($entries)>50) || ($manifest['target_pending']??null)!==count($entries)
       || ($manifest['source_commit']??'')!=='multisource-20261109')
        throw new RuntimeException('invalid_fifty_manifest');
    $pdo=\Celikom\Database\Connection::open($cfg);
    $lockId='celikom_blur_pending_batch_v1';
    $lockQ=$pdo->prepare('SELECT GET_LOCK(?,15)');
    $lockQ->execute([$lockId]);
    if((int)$lockQ->fetchColumn()!==1) throw new RuntimeException('another_import_in_progress');
    $locked=true;
    $inspector=new \Celikom\Application\Mp3Inspector();
    $storage=new \Celikom\Storage\LocalStorageAdapter($cfg['storage_path']);
    $tested=[];$seen=[];$nameKeys=[];$totalSize=0;
    foreach ($entries as $entry) {
        $id=$entry['id']??'';
        if(!is_string($id) || !preg_match('/^[1-9]\d{0,19}$/D',$id) || isset($seen[$id]))
            throw new RuntimeException('repeated_or_invalid_id');
        $seen[$id]=true;
        $artist=$entry['artist']??null;$title=$entry['title']??null;
        if(!is_string($artist)||!is_string($title)||trim($artist)===''||trim($title)===''
           || mb_strlen($artist)>240||mb_strlen($title)>240)
            throw new RuntimeException('invalid_source_label_'.$id);
        $titleKey=mb_strtolower(trim($artist).'|'.trim($title),'UTF-8');
        if(isset($nameKeys[$titleKey])) throw new RuntimeException('duplicate_title_in_batch_'.$id);
        $nameKeys[$titleKey]=true;
        $size=$entry['size']??0;$shaExpected=$entry['sha256']??'';
        if(!is_int($size)||$size<1024||$size>25000000||!is_string($shaExpected)||!preg_match('/^[a-f0-9]{64}$/D',$shaExpected))
            throw new RuntimeException('invalid_source_expected_hash_'.$id);
        $file=$stage.'/'.$id.'.mp3';
        if(!is_file($file)||is_link($file)||realpath($file)!==$file||filesize($file)!==$size)
            throw new RuntimeException('source_missing_or_size_'.$id);
        if(!hash_equals($shaExpected,hash_file('sha256',$file)))
            throw new RuntimeException('source_sha256_mismatch_'.$id);
        $mime=(new finfo(FILEINFO_MIME_TYPE))->file($file);
        $duration=$inspector->durationMs($file);
        if($mime!=='audio/mpeg'||$duration===null||abs($duration-(int)($entry['duration_ms']??0))>1500)
            throw new RuntimeException('source_mp3_validation_'.$id);
        $sha=hash_file('sha256',$file);
        if(!is_string($sha)||!hash_equals($shaExpected,$sha))
            throw new RuntimeException('source_sha256_'.$id);
        $tested[]=['id'=>$id,'artist'=>$artist,'title'=>$title,'size'=>$size,'file'=>$file,
            'sha'=>$sha,'key'=>'audio/'.substr($sha,0,2).'/'.$sha.'.mp3','duration'=>$duration];
        $totalSize+=$size;
    }
    $free=disk_free_space($cfg['storage_path']);
    if($free===false || $free < $totalSize+100000000)
        throw new RuntimeException('private_storage_capacity_insufficient');
    $findTrack=$pdo->prepare("SELECT id FROM tracks WHERE service='yandex' AND service_track_id=? LIMIT 1 FOR UPDATE");
    $findReq=$pdo->prepare("SELECT id FROM track_requests WHERE service='yandex' AND service_track_id=? LIMIT 1 FOR UPDATE");
    $findRemoved=$pdo->prepare("SELECT replacement_id FROM bulk_moderation_tombstones WHERE service='yandex' AND service_track_id=? LIMIT 1");
    $findSame=$pdo->prepare("SELECT service_track_id FROM tracks WHERE service='yandex' AND LOWER(TRIM(artist))=LOWER(TRIM(?)) AND LOWER(TRIM(title))=LOWER(TRIM(?)) LIMIT 1 FOR UPDATE");
    $findAsset=$pdo->prepare('SELECT id,storage_key,mime_type,size_bytes,duration_ms FROM audio_assets WHERE sha256=? LIMIT 1');
    $getMapping=$pdo->prepare("SELECT r.id,r.status,r.is_active,a.sha256 FROM track_replacements r
        JOIN audio_assets a ON a.id=r.audio_asset_id WHERE r.track_id=? ORDER BY r.id DESC LIMIT 1");
    $insertTrack=$pdo->prepare("INSERT INTO tracks(service,service_track_id,artist,title,album,duration_ms) VALUES ('yandex',?,?,?,?,?)");
    $insertAsset=$pdo->prepare("INSERT INTO audio_assets(storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms)
        VALUES('local',? ,?, 'audio/mpeg', ?,?)");
    $insertReplacement=$pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active,uploaded_by_user_id)
        VALUES(?,?,'pending',0,NULL)");
    foreach($tested as $item) {
        $id=$item['id'];
        $pdo->beginTransaction();
        $copied=false;
        try {
            $findTrack->execute([$id]);$existingId=$findTrack->fetchColumn();
            $findReq->execute([$id]);
            if($findReq->fetchColumn()!==false) throw new DomainException('request_exists_'.$id);
            $findRemoved->execute([$id]);
            if($findRemoved->fetchColumn()!==false) throw new DomainException('previously_deleted_'.$id);
            if($existingId!==false) {
                $getMapping->execute([(int)$existingId]);
                $r=$getMapping->fetch(PDO::FETCH_ASSOC);
                if($r && $r['sha256']===$item['sha'] && $r['status']==='pending' && (int)$r['is_active']===0) {
                    $resumed[]=['id'=>$id,'replacement_id'=>(int)$r['id']];
                    $pdo->commit();continue;
                }
                throw new DomainException('track_exists_or_changed_'.$id);
            }
            $findSame->execute([$item['artist'],$item['title']]);
            if($findSame->fetchColumn()!==false)throw new DomainException('title_exists_other_track_'.$id);
            $findAsset->execute([$item['sha']]);$asset=$findAsset->fetch(PDO::FETCH_ASSOC);
            if($asset && ($asset['storage_key']!==$item['key'] || $asset['mime_type']!=='audio/mpeg'
                 || (int)$asset['size_bytes']!==$item['size']
                 || abs((int)$asset['duration_ms']-$item['duration'])>1500))
                throw new DomainException('audio_asset_hash_conflict_'.$id);
            if($dry) {
                $new[]=['id'=>$id,'replacement_id'=>0];
                $pdo->rollBack();
                continue; // No filesystem, DB or moderation writes in dry run.
            }
            if(!$storage->exists($item['key'])) {
                $f=fopen($item['file'],'rb');
                if(!$f)throw new RuntimeException('mp3_open_error_'.$id);
                try{$storage->put($item['key'],$f);}
                finally{fclose($f);}
                $copied=true;
            }
            if($storage->getSize($item['key'])!==$item['size']
               || $storage->getMimeType($item['key'])!=='audio/mpeg')
                throw new RuntimeException('private_audio_not_matching_'.$id);
            $stream=$storage->openStream($item['key']);
            try { $existingSha=hash_init('sha256');hash_update_stream($existingSha,$stream); }
            finally { fclose($stream); }
            if(!hash_equals($item['sha'],hash_final($existingSha)))
                throw new RuntimeException('private_audio_digest_mismatch_'.$id);
            if($asset) $assetId=(int)$asset['id'];
            else {
                $insertAsset->execute([$item['key'],$item['sha'],$item['size'],$item['duration']]);
                $assetId=(int)$pdo->lastInsertId();
            }
            $insertTrack->execute([$id,$item['artist'],$item['title'],'',$item['duration']]);
            $trackId=(int)$pdo->lastInsertId();
            $insertReplacement->execute([$trackId,$assetId]);
            $new[]=['id'=>$id,'replacement_id'=>(int)$pdo->lastInsertId()];
            $pdo->commit();
        } catch(Throwable $e) {
            if($pdo->inTransaction())$pdo->rollBack();
            if($copied) {
                $q=$pdo->prepare('SELECT id FROM audio_assets WHERE sha256=? LIMIT 1');
                $q->execute([$item['sha']]);
                if($q->fetchColumn()===false) {
                    try{$storage->delete($item['key']);}catch(Throwable){}
                }
            }
            throw $e;
        }
    }
    if($dry) {
        echo json_encode(['status'=>'DRY_RUN_PASS','verified_files'=>count($tested),
            'possible_new'=>count($new),'matching_existing_pending'=>count($resumed),'writes'=>0,'rights_confirmed'=>false],
            JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
    } else {
        $post=$pdo->prepare("SELECT r.id,r.status,r.is_active FROM track_replacements r JOIN tracks t ON t.id=r.track_id
            WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.id DESC LIMIT 1");
        foreach(array_merge($new,$resumed) as $row) {
            $post->execute([$row['id']]);$actual=$post->fetch(PDO::FETCH_ASSOC);
            if(!$actual||$actual['status']!=='pending'||(int)$actual['is_active']!==0
               || (int)$actual['id']!==$row['replacement_id'])
                throw new RuntimeException('postcommit_pending_mismatch_'.$row['id']);
        }
        echo json_encode(['status'=>'PASS','requested'=>count($tested),'new_pending'=>count($new),'resumed'=>count($resumed),
            'approved'=>0,'active'=>0,'rights_confirmed'=>false,'bytes'=>$totalSize,'records'=>array_merge($new,$resumed)],
            JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
    }
} catch(Throwable $error) {
    if($pdo instanceof PDO && $pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,'BATCH50_IMPORT_REFUSED: '.$error->getMessage()."\n");
    exit(1);
} finally {
    if($locked && $pdo instanceof PDO) {
        try{$s=$pdo->prepare('SELECT RELEASE_LOCK(?)');$s->execute([$lockId]);}catch(Throwable){}
    }
}
