<?php

declare(strict_types=1);

/**
 * One-shot owner-only private staging -> pending moderation for twenty pinned
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
    ['id'=>'63104735','artist'=>'ZOVetik, Nemichieff','title'=>'Отключили свет','size'=>5665481,'blob'=>'50dd9780215d1ed1738df9749651e24eb9b60ad6'],
    ['id'=>'137472446','artist'=>'голодный','title'=>'таблетки','size'=>3887064,'blob'=>'b64d84cc063767488dae326fb5e296c6d2b9a3ec'],
    ['id'=>'150598645','artist'=>'uglystephan','title'=>'Я люблю лин','size'=>2065692,'blob'=>'24f50ada040137b03bee0d87d5ee2ce24bc01869'],
    ['id'=>'145054524','artist'=>'Пошлая Молли','title'=>'Спать с тобой','size'=>2489031,'blob'=>'3b9c85d9500d5777c6f9c9ccfdad9a6522367065'],
    ['id'=>'136272297','artist'=>'9mice','title'=>'indiana','size'=>4209938,'blob'=>'2768fdebf965d7bf3742d0c3ba14b9474b909298'],
    ['id'=>'123382745','artist'=>'Серега Пират','title'=>'В этой траве','size'=>5273643,'blob'=>'7602532ca321a46c1f85e1c76ab00dff5fa91cad'],
    ['id'=>'138778164','artist'=>'KSB muzic','title'=>'Отчим','size'=>3999912,'blob'=>'6cd86fd90493fc5ce824fcae762d3b405a738505'],
    ['id'=>'155025088','artist'=>'Clonnex','title'=>'ILD','size'=>4741566,'blob'=>'e14893f7d39e263700d1f6a3e374cc6c4b2afe49'],
    ['id'=>'137300017','artist'=>'madk1d','title'=>'так похуй','size'=>4445732,'blob'=>'4f5c70355dd19103bc16240aa48228ee12e9dea2'],
    ['id'=>'93401053','artist'=>'Паша Техник','title'=>'Я ебал в рот','size'=>7204614,'blob'=>'63d58a21e5eb2bef667158b8068d05afae658dfc'],
    ['id'=>'151855603','artist'=>'CUPSIZE','title'=>'мы делили апельсин','size'=>2840520,'blob'=>'e25bc6bed68c6a3b0ace51b1f9ef6e24c60916d3'],
    ['id'=>'152396542','artist'=>'Пошлая Молли','title'=>'Lin Ansty','size'=>6168162,'blob'=>'a26ded76e0f7bb8f53b8ef1e2d196b3ee1095d15'],
    ['id'=>'136404135','artist'=>'Пошлая Молли','title'=>'Школа не нужна','size'=>3772370,'blob'=>'661fd8e83a0c1b37a433e280a44d5bc3f76c66f2'],
    ['id'=>'138629224','artist'=>'Расстройство','title'=>'Виновата скорость','size'=>5380792,'blob'=>'b5527c5e51e1db86f582298a7bf163bdcdb6aa52'],
    ['id'=>'110374527','artist'=>'Lida, СТИНТ, mazzellovvv, ШАПКА, t2x2, Барагозеры','title'=>'Новогодняя','size'=>5137807,'blob'=>'0b5af9892857ae9b124608112159bc3697282390'],
    ['id'=>'149870633','artist'=>'Синдром Восьмиклассника','title'=>'ДЖЕТИКС','size'=>3620684,'blob'=>'4c8dec4fe716009803f21996a7c80b959ad5ffa3'],
    ['id'=>'30212997','artist'=>'Yanix, ATL','title'=>'Трэп хата','size'=>3236257,'blob'=>'d328c2c2c097c12ae26fd5462039bddb03634e13'],
    ['id'=>'111001121','artist'=>'две тысячи ярдов','title'=>'Постарели','size'=>4983162,'blob'=>'c646ac8536962e555ff89043d750cad21c0b361c'],
    ['id'=>'120305632','artist'=>'CUPSIZE','title'=>'Клей','size'=>3485615,'blob'=>'66362788000bee592e5d1e27d38f26c35f28939b'],
    ['id'=>'63607797','artist'=>'4К','title'=>'Крайне аккуратно','size'=>7901562,'blob'=>'9a42e596cfb67da1a8535dd3e7b109e64a2ed1e1'],
];

$copied = [];
$pdo = null;
try {
    if (is_link($stage) || !preg_match('~^' . preg_quote($base, '~') . '/incoming/blur-twenty-[0-9]{8,16}$~D', $stage)
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
    if (count($entries) !== 20) throw new RuntimeException('wrong_batch_size');
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
        if ($duration === null || $duration < 1000 || $duration > 86400000) {
            throw new RuntimeException('mp3_duration_failed_' . $entry['id']);
        }
        $mime = (new finfo(FILEINFO_MIME_TYPE))->file($file);
        if ($mime !== 'audio/mpeg') throw new RuntimeException('mp3_mime_failed_' . $entry['id']);
        $sha256 = hash_file('sha256', $file);
        if (!is_string($sha256) || strlen($sha256) !== 64) throw new RuntimeException('audio_digest_failed_' . $entry['id']);
        $fingerprints[$entry['id']] = ['file'=>$file,'sha'=>$sha256,'key'=>'audio/' . substr($sha256,0,2) . '/' . $sha256 . '.mp3','duration'=>$duration];
    }

    // Zero DB writes until all twenty files are verified. Refuse any existing
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