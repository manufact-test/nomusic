<?php

declare(strict_types=1);

/**
 * One-shot owner-only private staging -> pending moderation for five pinned
 * source MP3 files. Never approves or activates. No web/public endpoint.
 * Caller runs this file via SSH inside a temporary private incoming directory.
 */

if (PHP_SAPI !== 'cli' || count($argv) !== 1) {
    fwrite(STDERR, "ERROR: cli_only\n");
    exit(2);
}
ini_set('display_errors', '0');
error_reporting(E_ALL);

$base = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$stage = __DIR__;
$entries = [
    ['id'=>'17198343','artist'=>'Сектор Газа','title'=>'Опять сегодня','size'=>5690514,'blob'=>'a900564ca1581a1e3686f4cc22a8e6461f302465','duration'=>142263],
    ['id'=>'24442524','artist'=>'Агата Кристи','title'=>'Моряк','size'=>8796967,'blob'=>'430d56493268e927c5fa17531818c15131742c06','duration'=>217496],
    ['id'=>'27323567','artist'=>'GUF','title'=>'Ice Baby','size'=>10176701,'blob'=>'8bed6b5391b3e3272463cec8002187f8c68887b6','duration'=>252238],
    ['id'=>'29851850','artist'=>'PHARAOH','title'=>'Black Siemens','size'=>7697180,'blob'=>'ca26ff6dc980f758af2113aa036b8cc27aced94d','duration'=>190276],
    ['id'=>'25168288','artist'=>'ЛСП','title'=>'Уровни','size'=>9535135,'blob'=>'eef7b5cfbd68d747ee18bd832cd28fda4d5107de','duration'=>236199],
];

$copied = [];
$pdo = null;
try {
    if (is_link($stage) || !preg_match('~^' . preg_quote($base, '~') . '/incoming/blur-five-[0-9]{8,16}$~D', $stage)
        || realpath($stage) !== $stage || !is_dir($stage)) {
        throw new RuntimeException('invalid_private_staging');
    }
    $release = realpath($base . '/current');
    if (!is_link($base . '/current') || $release === false
        || !str_starts_with($release, $base . '/releases/')
        || !is_file($release . '/bootstrap.php') || !is_file($release . '/config/app.php')) {
        throw new RuntimeException('unexpected_active_release');
    }
    require_once $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['environment'] !== 'production' || $config['storage_driver'] !== 'local'
        || realpath((string) $config['storage_path']) !== $base . '/shared/audio'
        || !is_dir($config['storage_path'])) {
        throw new RuntimeException('unexpected_private_configuration');
    }
    $pdo = \Celikom\Database\Connection::open($config);
    $inspector = new \Celikom\Application\Mp3Inspector();
    $fingerprints = [];
    foreach ($entries as $entry) {
        $file = $stage . '/' . $entry['id'] . '.mp3';
        if (!is_file($file) || is_link($file) || realpath($file) !== $file
            || filesize($file) !== $entry['size']) {
            throw new RuntimeException('missing_or_wrong_size_' . $entry['id']);
        }
        $gitHasher = hash_init('sha1');
        hash_update($gitHasher, 'blob ' . $entry['size'] . "\0");
        $fh = fopen($file, 'rb');
        if ($fh === false) throw new RuntimeException('unreadable_source_' . $entry['id']);
        try {
            while (!feof($fh)) {
                $chunk = fread($fh, 262144);
                if ($chunk === false) throw new RuntimeException('unreadable_chunk_' . $entry['id']);
                hash_update($gitHasher, $chunk);
            }
        } finally { fclose($fh); }
        if (!hash_equals($entry['blob'], hash_final($gitHasher))) {
            throw new RuntimeException('source_integrity_failed_' . $entry['id']);
        }
        $duration = $inspector->durationMs($file);
        if ($duration === null || abs($duration - $entry['duration']) > 1500) {
            throw new RuntimeException('mp3_duration_failed_' . $entry['id']);
        }
        $mime = (new finfo(FILEINFO_MIME_TYPE))->file($file);
        if ($mime !== 'audio/mpeg') throw new RuntimeException('mp3_mime_failed_' . $entry['id']);
        $sha256 = hash_file('sha256', $file);
        if (!is_string($sha256) || strlen($sha256) !== 64) throw new RuntimeException('audio_digest_failed_' . $entry['id']);
        $fingerprints[$entry['id']] = ['file'=>$file,'sha'=>$sha256,'key'=>'audio/' . substr($sha256,0,2) . '/' . $sha256 . '.mp3','duration'=>$duration];
    }

    // Zero DB writes until all five files are verified. Refuse any existing
    // exact track, moderation request or same-titled same-artist candidate.
    $pdo->beginTransaction();
    $found = $pdo->prepare("SELECT id FROM tracks WHERE service='yandex' AND service_track_id = ? LIMIT 1 FOR UPDATE");
    $req = $pdo->prepare("SELECT id FROM track_requests WHERE service='yandex' AND service_track_id = ? LIMIT 1 FOR UPDATE");
    $same = $pdo->prepare("SELECT service_track_id FROM tracks WHERE service='yandex' AND LOWER(TRIM(artist)) = LOWER(TRIM(?)) AND LOWER(TRIM(title)) = LOWER(TRIM(?)) LIMIT 1 FOR UPDATE");
    foreach ($entries as $entry) {
        $found->execute([$entry['id']]);
        $req->execute([$entry['id']]);
        $same->execute([$entry['artist'], $entry['title']]);
        if ($found->fetchColumn() !== false || $req->fetchColumn() !== false || $same->fetchColumn() !== false) {
            throw new RuntimeException('existing_track_or_request_' . $entry['id']);
        }
    }

    if (getenv('CELIKOM_BLUR_DRY_RUN') === '1') {
        $pdo->rollBack();
        echo json_encode(['status'=>'DRY_RUN_PASS','candidate_count'=>count($entries),'existing_records'=>0,'writes'=>0], JSON_THROW_ON_ERROR), "\n";
        exit(0);
    }

    $storage = new \Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    $newRows = [];
    $insertTrack = $pdo->prepare("INSERT INTO tracks (service,service_track_id,artist,title,album,duration_ms) VALUES ('yandex',?,?,?,?,?)");
    $getAsset = $pdo->prepare('SELECT id, storage_key, mime_type, size_bytes, duration_ms FROM audio_assets WHERE sha256=? LIMIT 1');
    $insertAsset = $pdo->prepare("INSERT INTO audio_assets (storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms) VALUES ('local',? ,?, 'audio/mpeg', ?, ?)");
    $insertReplacement = $pdo->prepare("INSERT INTO track_replacements (track_id,audio_asset_id,status,is_active,uploaded_by_user_id) VALUES (?,?,'pending',0,NULL)");
    foreach ($entries as $entry) {
        $data = $fingerprints[$entry['id']];
        $getAsset->execute([$data['sha']]);
        $existing = $getAsset->fetch(PDO::FETCH_ASSOC);
        if ($existing && ($existing['storage_key'] !== $data['key'] || $existing['mime_type'] !== 'audio/mpeg'
            || (int)$existing['size_bytes'] !== $entry['size'] || abs((int)$existing['duration_ms']-$data['duration'])>1500)) {
            throw new RuntimeException('audio_asset_conflict_' . $entry['id']);
        }
        if (!$storage->exists($data['key'])) {
            $fh = fopen($data['file'], 'rb');
            if ($fh === false) throw new RuntimeException('source_open_failed_' . $entry['id']);
            try { $storage->put($data['key'], $fh); }
            finally { fclose($fh); }
            $copied[] = $data['key'];
        }
        if ($storage->getSize($data['key']) !== $entry['size']) {
            throw new RuntimeException('private_asset_size_conflict_' . $entry['id']);
        }
        $assetId = 0;
        if ($existing) {
            $assetId = (int)$existing['id'];
        } else {
            $insertAsset->execute([$data['key'], $data['sha'], $entry['size'], $data['duration']]);
            $assetId = (int) $pdo->lastInsertId();
        }
        $insertTrack->execute([$entry['id'], $entry['artist'], $entry['title'], '', $data['duration']]);
        $trackId = (int) $pdo->lastInsertId();
        $insertReplacement->execute([$trackId, $assetId]);
        $newRows[] = ['track_id'=>$entry['id'],'replacement_id'=>(int)$pdo->lastInsertId(),'status'=>'pending','is_active'=>0];
    }
    $pdo->commit();
    $copied = []; // No cleanup of valid pending assets after successful commit.
    $check = $pdo->prepare("SELECT r.id,r.status,r.is_active,t.service_track_id FROM track_replacements r JOIN tracks t ON t.id=r.track_id WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.id DESC LIMIT 1");
    foreach ($newRows as &$row) {
        $check->execute([$row['track_id']]);
        $actual = $check->fetch(PDO::FETCH_ASSOC);
        if (!$actual || $actual['status']!=='pending' || (int)$actual['is_active']!==0 || (int)$actual['id']!==$row['replacement_id']) {
            throw new RuntimeException('postcommit_pending_verification_failed_' . $row['track_id']);
        }
    }
    unset($row);
    echo json_encode(['status'=>'PASS','pending_created'=>count($newRows),'approved'=>0,'active'=>0,'production_changed'=>true,
        'rights_confirmed'=>false,'import_source'=>'FckCensorData pinned Git commit','records'=>$newRows],
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR), "\n";
} catch (Throwable $e) {
    if ($pdo instanceof PDO && $pdo->inTransaction()) $pdo->rollBack();
    if (isset($storage)) {
        foreach ($copied as $key) { try {$storage->delete($key);}catch(Throwable){} }
    }
    fwrite(STDERR, "PENDING_IMPORT_FAILED: " . $e->getMessage() . "\n");
    exit(1);
}