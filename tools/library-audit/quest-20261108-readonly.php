<?php
declare(strict_types=1);
/**
 * CELIKOM 2026-11-08: production SELECT-only audit of Quest Pistols and
 * cross-artist duplicate mapping during bulk uploads.
 *
 * Never changes data, files, users or credentials. No audio bytes in output.
 * Runs once over SSH stdin (no on-server script install).
 */
if (PHP_SAPI !== 'cli' || count($argv) !== 1) exit(2);
ini_set('display_errors', '0');
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$pdo=null;
try {
    $release=realpath($base.'/current');
    if (!is_link($base.'/current') || !$release || !str_starts_with($release,$base.'/releases/'))
        throw new RuntimeException('unsafe_current_release');
    require_once $release.'/bootstrap.php';
    $cfg=require $release.'/config/app.php';
    if (($cfg['environment']??'')!=='production'||($cfg['storage_driver']??'')!=='local')
        throw new RuntimeException('not_production_local_storage');
    $pdo=\Celikom\Database\Connection::open($cfg);
    $pdo->exec('START TRANSACTION READ ONLY');

    $q=$pdo->query("SELECT t.id AS db_track_id,t.service_track_id,t.title,t.artist,t.album,t.duration_ms,
             t.created_at AS track_created_at,r.id AS replacement_id,r.status,r.is_active,
             r.created_at AS replacement_created_at,r.approved_at,r.disabled_at,
             a.duration_ms AS asset_duration_ms,a.size_bytes,LEFT(a.sha256,12) AS asset_sha_prefix
          FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id
          LEFT JOIN audio_assets a ON a.id=r.audio_asset_id
          WHERE t.service='yandex' AND (
             LOWER(t.artist) LIKE '%quest%pistol%'
             OR LOWER(t.title) LIKE '%он рядом%')
          ORDER BY t.service_track_id,r.id LIMIT 100");
    $quest=$q->fetchAll(PDO::FETCH_ASSOC);
    $questOut=[];
    foreach($quest as $row){
        $out=$row;
        foreach(['db_track_id','replacement_id','duration_ms','asset_duration_ms','size_bytes','is_active'] as $field)
            $out[$field]=isset($row[$field])?(int)$row[$field]:null;
        $out['source_quest_224520ms_match']=mb_strtolower(trim((string)$out['title']),'UTF-8')==='он рядом'
            && abs($out['duration_ms']-224520)<=1000;
        $questOut[]=$out;
    }

    $sql="SELECT t.service_track_id,t.artist,t.title,t.duration_ms,r.id AS replacement_id,
               r.status,r.is_active,a.duration_ms AS asset_duration_ms
            FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id
            LEFT JOIN audio_assets a ON a.id=r.audio_asset_id
            WHERE t.service='yandex' ORDER BY t.id,r.id";
    $all=$pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC);
    $ids=[];$activeById=[];$assetDurationProblems=[];$groups=[];$questCount=0;
    foreach($all as $r){
        $id=(string)$r['service_track_id'];
        if(!isset($ids[$id]))$ids[$id]=1;
        if((string)$r['status']==='approved'&&(int)$r['is_active']===1)$activeById[$id]=($activeById[$id]??0)+1;
        if($r['replacement_id']!==null && $r['asset_duration_ms']!==null &&
           abs((int)$r['duration_ms']-(int)$r['asset_duration_ms'])>1500){
            $assetDurationProblems[]=['track_id'=>$id,'replacement_id'=>(int)$r['replacement_id'],
              'source_ms'=>(int)$r['duration_ms'],'file_ms'=>(int)$r['asset_duration_ms']];
        }
        $title=mb_strtolower(trim(preg_replace('/\s+/u',' ',(string)$r['title'])),'UTF-8');
        $artist=mb_strtolower(trim(preg_replace('/\s+/u',' ',(string)$r['artist'])),'UTF-8');
        $key=$artist."\0".$title;
        if(!isset($groups[$key]))$groups[$key]=['artist'=>$r['artist'],'title'=>$r['title'],'ids'=>[],
          'active'=>0,'pending'=>0];
        $groups[$key]['ids'][$id]=true;
        if((int)$r['is_active']===1)$groups[$key]['active']++;
        if((string)$r['status']==='pending')$groups[$key]['pending']++;
    }
    $duplicateNames=[];
    foreach($groups as $g)if(count($g['ids'])>1){
        $duplicateNames[]=['artist'=>$g['artist'],'title'=>$g['title'],
          'track_ids'=>array_keys($g['ids']),'active_replacements'=>$g['active'],
          'pending_replacements'=>$g['pending']];
    }
    $sameIdActiveConflicts=array_filter($activeById,static fn($count)=>$count>1);
    $pdo->rollBack();

    echo json_encode([
      'type'=>'CELIKOM_QUEST_LIBRARY_AUDIT_READ_ONLY',
      'checked_at_utc'=>gmdate('c'),
      'quest_or_named_source_rows'=>$questOut,
      'yandex_unique_track_ids'=>count($ids),
      'replacement_rows_inspected'=>count($all),
      'same_track_id_multiple_active'=>count($sameIdActiveConflicts),
      'same_track_id_multiple_active_ids'=>array_keys($sameIdActiveConflicts),
      'different_track_id_same_normalized_artist_title_groups'=>count($duplicateNames),
      'different_track_id_same_normalized_artist_title_examples'=>array_slice($duplicateNames,0,40),
      'replacement_vs_source_duration_gt1500ms_count'=>count($assetDurationProblems),
      'replacement_vs_source_duration_gt1500ms_examples'=>array_slice($assetDurationProblems,0,40),
      'writes'=>0
    ],JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR),"\n";
} catch (Throwable $e) {
    if($pdo instanceof PDO && $pdo->inTransaction()) $pdo->rollBack();
    fwrite(STDERR,'CELIKOM_QUEST_AUDIT_REFUSED: '.$e->getMessage()."\n");
    exit(2);
}
