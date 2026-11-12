<?php
declare(strict_types=1);
/*
 * W77: identify incident track IDs, approved asset size and encoded nominal bitrates, without playing audio, no audio served, no user data.
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
    echo "W77_ACTIVE_RELEASE=".basename($release)."\n";
    echo "W77_UTC=".gmdate('Y-m-d H:i:s')."\n";
    $q=$db->prepare(
        "SELECT t.service_track_id,t.artist,t.title,t.album,t.duration_ms AS listed_ms,
            r.id AS replacement_id,r.status,r.is_active,r.disabled_at,
            r.version,a.mime_type,a.duration_ms AS asset_ms,a.size_bytes
         FROM tracks t
         LEFT JOIN track_replacements r ON r.track_id=t.id
         LEFT JOIN audio_assets a ON a.id=r.audio_asset_id
         WHERE t.service='yandex' AND (
           t.service_track_id IN ('103624638','59633283','102494056','126749933')
           OR LOWER(t.artist) LIKE '%кишлак%'
           OR LOWER(t.title) LIKE '%самый лучший день%'
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
        echo 'W77_TRACK '.json_encode([
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
    echo "W77_MATCHED_ROWS=".count($seen)."\n";
    $q=$db->query(
        "SELECT
           COUNT(*) AS total_tracks,
           COUNT(DISTINCT CASE WHEN r.id IS NOT NULL AND r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL THEN t.id END) AS active,
           COUNT(DISTINCT CASE WHEN r.id IS NOT NULL AND r.status='approved' AND r.is_active=0 THEN t.id END) AS approved_inactive
         FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id
         WHERE t.service='yandex'");
    echo 'W77_LIBRARY_COUNTS '.json_encode($q->fetch(\PDO::FETCH_ASSOC))."\n";
    $db->rollBack();
    echo "W77_LIVE_CATALOG_SELECT_ONLY_PASS\n";
} catch (\Throwable $e) {
    if(isset($db) && $db->inTransaction()) $db->rollBack();
    fwrite(STDERR,"W77_AUDIT_FAILED_CLASS=".get_class($e)."\n");
    exit(1);
}
