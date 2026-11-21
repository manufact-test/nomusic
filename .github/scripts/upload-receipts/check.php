<?php

declare(strict_types=1);
$root = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$live = realpath($root . '/current');
if ($live === false || !str_starts_with($live, $root . '/releases/')) throw new RuntimeException('release');
require $live . '/bootstrap.php';
$config = require $live . '/config/app.php';
$pdo = Celikom\Database\Connection::open($config);
$pdo->exec('SET TRANSACTION READ ONLY');
$pdo->beginTransaction();
try {
    $rows = $pdo->query("SELECT r.id,r.status,r.created_at,t.artist,t.title,t.service_track_id,t.duration_ms AS original_duration_ms,
        a.storage_key,a.sha256,a.size_bytes,a.duration_ms,a.mime_type,
        (SELECT COUNT(*) FROM upload_submissions u WHERE u.replacement_id=r.id) AS submissions
        FROM track_replacements r JOIN tracks t ON t.id=r.track_id JOIN audio_assets a ON a.id=r.audio_asset_id
        WHERE r.created_at >= '2026-11-21 07:31:00' ORDER BY r.id DESC LIMIT 25")->fetchAll(PDO::FETCH_ASSOC);
    $storage = new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    $results = [];
    foreach ($rows as $row) {
        $key = $row['storage_key']; unset($row['storage_key']);
        try {
            $stream = $storage->openStream($key);
            try {
                $path = stream_get_meta_data($stream)['uri'];
                $hash = hash_init('sha256'); hash_update_stream($hash, $stream);
                $row['stored_hash_ok'] = hash_final($hash) === $row['sha256'];
                $row['stored_size_ok'] = $storage->getSize($key) === (int)$row['size_bytes'];
                if ($row['mime_type'] === 'audio/mpeg') {
                    $measured = (new Celikom\Application\Mp3Inspector())->durationMs($path);
                    $row['measured_ms'] = $measured;
                    $row['duration_ok'] = $measured !== null && abs($measured - (int)$row['original_duration_ms']) <= 1500;
                    $prepared = (new Celikom\Application\Mp3Normalizer())->prepare($path);
                    try { $row['already_clean'] = hash_file('sha256', $prepared['path']) === $row['sha256']; }
                    finally { unlink($prepared['path']); }
                    (new Celikom\Application\Mp3DecodeValidator())->check($path);
                    $row['full_decode_ok'] = true;
                }
                $row['checked'] = true;
            } finally { fclose($stream); }
        } catch (Throwable $e) { $row['checked'] = false; $row['check_error'] = get_class($e) . ':' . $e->getMessage(); }
        $results[] = $row;
    }
    echo json_encode(['at_utc'=>gmdate('c'),'active_release'=>basename($live),'recent_uploads'=>$results], JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
} finally { $pdo->rollBack(); }
