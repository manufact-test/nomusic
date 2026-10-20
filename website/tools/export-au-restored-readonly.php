<?php
declare(strict_types=1);
/**
 * Website demo-only read-only export of the existing approved Au replacement.
 *
 * CLI only on the already-authorized Hostinger account. No database writes,
 * new media mappings, track changes, source renames or extension file edits.
 * On success STDOUT is strictly MP3 bytes; no signed URLs or credentials.
 */
if (PHP_SAPI!=='cli' || count($argv)!==1)exit(2);
ini_set('display_errors','0');
try {
    $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release=realpath($root.'/current');
    if ($release===false || !str_starts_with($release,$root.'/releases/')) {
        throw new RuntimeException('Unexpected release root');
    }
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    if (($config['storage_driver']??'')!=='local')throw new RuntimeException('Storage driver mismatch');
    $pdo=\Celikom\Database\Connection::open($config);
    $pdo->exec('SET TRANSACTION READ ONLY');
    $pdo->beginTransaction();
    $stmt=$pdo->prepare(
        "SELECT t.service_track_id,t.title,t.artist,t.duration_ms original_ms,".
        "a.sha256,a.size_bytes,a.storage_key FROM tracks t ".
        "JOIN track_replacements r ON r.track_id=t.id ".
        "JOIN audio_assets a ON a.id=r.audio_asset_id ".
        "WHERE t.service='yandex' AND t.service_track_id=? ".
        "AND r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL"
    );
    $stmt->execute(['144530503']);
    $rows=$stmt->fetchAll(\PDO::FETCH_ASSOC);
    $pdo->commit();
    if (count($rows)!==1)throw new RuntimeException('Not exactly one active version');
    $r=$rows[0];
    if ((int)$r['original_ms']!==180872 ||
        !str_contains(mb_strtolower((string)$r['title'],'UTF-8'),'ау') ||
        (int)$r['size_bytes']<1000000 || (int)$r['size_bytes']>30000000 ||
        !preg_match('/^[a-f0-9]{64}$/D',(string)$r['sha256'])) {
        throw new RuntimeException('Track identity does not match owner file');
    }
    $storage=new \Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    if ($storage->getSize($r['storage_key'])!==(int)$r['size_bytes']) {
        throw new RuntimeException('Source size mismatch');
    }
    $stream=$storage->openStream($r['storage_key']);
    if (!is_resource($stream))throw new RuntimeException('Cannot read source');
    $hash=hash_init('sha256');
    hash_update_stream($hash,$stream);
    if (!hash_equals((string)$r['sha256'],hash_final($hash)) || rewind($stream)!==true) {
        throw new RuntimeException('Source checksum mismatch');
    }
    fpassthru($stream);
    fclose($stream);
} catch (\Throwable $error) {
    fwrite(STDERR,"Read-only demo source unavailable; existing recording untouched.\n");
    exit(1);
}
