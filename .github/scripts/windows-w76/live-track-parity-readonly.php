<?php
declare(strict_types=1);
/*
 * W76: live catalog metadata audit, no audio served, no user data.
 * SQL SELECT-only, no production writes, no credentials printed.
 */
ini_set('display_errors','0');
try {
    if (PHP_SAPI !== 'cli') throw new RuntimeException('wrong_sapi');
    $base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    if (!is_link($base.'/current')) throw new RuntimeException('missing_current');
    $release=realpath($base.'/current');
    if (!is_string($release) || !str_starts_with($release,$base.'/releases/'))
        throw new RuntimeException('release_guard');
    require $release.'/bootstrap.php';
    $cfg=require $release.'/config/app.php';
    if (($cfg['environment']??'')!=='production' || !($cfg['auth_enabled']??false))
        throw new RuntimeException('env_guard');
    $db=\Celikom\Database\Connection::open($cfg);
    $db->exec('SET TRANSACTION READ ONLY');
    $db->beginTransaction();
    echo "W76_ACTIVE_RELEASE=".basename($release)."\n";
    echo "W76_UTC=".gmdate('Y-m-d H:i:s')."\n";
    $q=$db->prepare(
        "SELECT t.service_track_id,t.artist,t.title,t.album,t.duration_ms AS listed_ms,
            r.id AS replacement_id,r.status,r.is_active,r.disabled_at,
            r.version,a.mime_type,a.duration_ms AS asset_ms,a.size_bytes
         FROM tracks t
         LEFT JOIN track_replacements r ON r.track_id=t.id
         LEFT JOIN audio_assets a ON a.id=r.audio_asset_id
         WHERE t.service='yandex' AND (
           t.service_track_id IN ('106040459','27323616','144530503','40371622')
           OR (LOWER(t.artist) LIKE '%карат%' AND LOWER(TRIM(t.title)) IN ('ты','ты (acoustic version)'))
         )
         ORDER BY t.title,t.artist,t.service_track_id,r.id
         LIMIT 100");
    $q->execute();
    $seen=[];
    foreach($q->fetchAll(\PDO::FETCH_ASSOC) as $row) {
        $id=$row['service_track_id'];
        $key=$id.':'.($row['replacement_id']??'none');
        if(isset($seen[$key])) continue;
        $seen[$key]=true;
        // Only public catalog metadata, no tokens, files, users or asset hashes.
        echo 'W76_TRACK '.json_encode([
            'id'=>$id,'artist'=>mb_substr((string)$row['artist'],0,120),
            'title'=>mb_substr((string)$row['title'],0,120),
            'album'=>mb_substr((string)$row['album'],0,90),
            'listed_ms'=>(int)$row['listed_ms'],
            'replacement_id'=>isset($row['replacement_id'])?(int)$row['replacement_id']:null,
            'status'=>$row['status'],'active'=>(int)$row['is_active'],
            'disabled'=>$row['disabled_at']!==null,
            'asset_ms'=>isset($row['asset_ms'])?(int)$row['asset_ms']:null,
            'mime'=>$row['mime_type'],
            'asset_bytes'=>isset($row['size_bytes'])?(int)$row['size_bytes']:null,
        ],JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE)."\n";
    }
    echo "W76_MATCHED_ROWS=".count($seen)."\n";
    $q=$db->query(
        "SELECT
           COUNT(*) AS total_tracks,
           COUNT(DISTINCT CASE WHEN r.id IS NOT NULL AND r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL THEN t.id END) AS active,
           COUNT(DISTINCT CASE WHEN r.id IS NOT NULL AND r.status='approved' AND r.is_active=0 THEN t.id END) AS approved_inactive
         FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id
         WHERE t.service='yandex'");
    echo 'W76_LIBRARY_COUNTS '.json_encode($q->fetch(\PDO::FETCH_ASSOC))."\n";
    $q=$db->query(
        "SELECT LOWER(TRIM(t.artist)) AS artist_key,LOWER(TRIM(t.title)) AS title_key,
                COUNT(DISTINCT t.service_track_id) AS ids,
                GROUP_CONCAT(DISTINCT t.service_track_id ORDER BY t.service_track_id SEPARATOR ',') AS all_ids,
                GROUP_CONCAT(DISTINCT CASE WHEN r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL THEN t.service_track_id END ORDER BY t.service_track_id SEPARATOR ',') AS active_ids
         FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id
         WHERE t.service='yandex'
         GROUP BY LOWER(TRIM(t.artist)),LOWER(TRIM(t.title))
         HAVING ids > 1 AND active_ids IS NOT NULL
         ORDER BY ids DESC LIMIT 25");
    foreach($q->fetchAll(\PDO::FETCH_ASSOC) as $row) {
        $all=explode(',',(string)$row['all_ids']);
        $active=explode(',',(string)$row['active_ids']);
        if(count($all)>count($active)) {
            echo 'W76_DUPLICATE_PARTIAL '.json_encode([
                'artist'=>mb_substr((string)$row['artist_key'],0,100),
                'title'=>mb_substr((string)$row['title_key'],0,100),
                'all_ids'=>array_slice($all,0,12),
                'active_ids'=>array_slice($active,0,12),
            ],JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE)."\n";
        }
    }
    $db->rollBack();
    echo "W76_LIVE_CATALOG_SELECT_ONLY_PASS\n";
} catch (\Throwable $e) {
    if(isset($db) && $db->inTransaction()) $db->rollBack();
    fwrite(STDERR,"W76_AUDIT_FAILED_CLASS=".get_class($e)."\n");
    exit(1);
}
