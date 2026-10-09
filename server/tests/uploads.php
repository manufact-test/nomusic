<?php

declare(strict_types=1);

require __DIR__ . '/smoke.php';

use Celikom\Application;
use Celikom\Application\UploadService;
use Celikom\Application\DeferredFingerprintService;
use Celikom\Application\TrackRequestService;
use Celikom\Application\UploadRateLimiter;
use Celikom\Application\Mp3Inspector;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Repositories\PdoCatalogRepository;
use Celikom\Storage\LocalStorageAdapter;

$config = require dirname(__DIR__) . '/config/app.php';
if (!str_starts_with((string) $config['db_name'], 'celikom_test')) {
    if (getenv('CI')) throw new RuntimeException('Upload tests require disposable celikom_test*');
    fwrite(STDOUT, "Stage 7 MySQL tests deferred.\n");
    exit(0);
}
$pdo = Connection::open($config);
(new MigrationRunner($pdo, dirname(__DIR__) . '/migrations'))->run();
$storage = new LocalStorageAdapter($config['storage_path']);
$ownerHash = hash('sha256', 'stage7-ci-isolated-owner');
$path = sys_get_temp_dir() . '/celikom-stage7-' . bin2hex(random_bytes(8)) . '.mp3';
// Synthetic MP3 frame stream: MPEG1 Layer3, 128 kbps, 44.1 kHz.
// No copyrighted audio or live library asset is involved.
$frame = hex2bin('fffb9064') . str_repeat("\0", 413);
file_put_contents($path, str_repeat($frame, 100));
$size = filesize($path);
$fields = [
    'service' => 'yandex', 'track_id' => '799001', 'duration_ms' => '2606',
    'artist' => 'synthetic', 'title' => 'stage7', 'album' => '', 'declaration' => '1',
    'request_id' => '10000000-0000-4000-8000-000000000001',
];
$file = ['error' => UPLOAD_ERR_OK, 'tmp_name' => $path, 'name' => 'audio.mp3', 'size' => $size];
$service = new UploadService($pdo, $storage, 31457280, static fn (string $p): bool => is_file($p),
    new DeferredFingerprintService($pdo));
$catalog = new PdoCatalogRepository($pdo);

try {
    run('Stage 7 structural MP3 probe accepts synthetic frames', function () use ($path): void {
        expect((new Mp3Inspector())->check($path), 'Synthetic MPEG frames');
    });
    $created = $service->upload($fields, $file, $ownerHash);
    run('Stage 7 upload creates only pending candidate and fingerprint job', function () use ($pdo, $catalog, $created): void {
        expect($created['status'] === 'pending' && !$created['duplicate'], 'Only pending');
        expect($catalog->findActive('yandex', '799001') === null, 'No active replacement');
        expect($catalog->findByReplacement((int) $created['replacement_id']) === null, 'No public audio');
        $stmt = $pdo->prepare('SELECT r.status, r.is_active, f.status AS fingerprint_status FROM track_replacements r
            JOIN audio_fingerprint_jobs f ON f.audio_asset_id = r.audio_asset_id WHERE r.id = ?');
        $stmt->execute([$created['replacement_id']]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        expect($row['status'] === 'pending' && (int) $row['is_active'] === 0 && $row['fingerprint_status'] === 'pending',
            'Pending and deferred fingerprint only');
    });
    run('Stage 7 byte-identical upload under different name and same request is idempotent', function () use ($service, $fields, $file, $ownerHash, $created, $pdo): void {
        $again = $service->upload($fields, array_merge($file, ['name' => 'renamed.mp3']), $ownerHash);
        expect($again['duplicate'] && $again['replacement_id'] === $created['replacement_id'], 'Idempotency key');
        $differentId = array_merge($fields, ['request_id' => '10000000-0000-4000-8000-000000000002']);
        $renamed = $service->upload($differentId, array_merge($file, ['name' => 'another-name.mp3']), $ownerHash);
        expect($renamed['duplicate'] && $renamed['replacement_id'] === $created['replacement_id'], 'SHA candidate dedupe');
        expect((int) $pdo->query("SELECT COUNT(*) FROM track_replacements r
            JOIN tracks t ON t.id = r.track_id WHERE t.service_track_id = '799001'")->fetchColumn() === 1,
            'No second candidate');
    });
    run('Stage 7 same asset links second exact Track ID without publication', function () use ($service, $fields, $file, $ownerHash, $pdo, $catalog, $created): void {
        $second = $service->upload(array_merge($fields, [
            'track_id' => '799002', 'request_id' => '10000000-0000-4000-8000-000000000003'
        ]), $file, $ownerHash);
        expect($second['replacement_id'] !== $created['replacement_id'], 'Different candidate link');
        $stmt = $pdo->prepare('SELECT audio_asset_id FROM track_replacements WHERE id IN (?, ?) ORDER BY id');
        $stmt->execute([$created['replacement_id'], $second['replacement_id']]);
        $ids = $stmt->fetchAll(PDO::FETCH_COLUMN);
        expect(count($ids) === 2 && $ids[0] === $ids[1], 'One reusable asset');
        expect($catalog->findActive('yandex', '799002') === null, 'Still pending');
        $sha = hash_file('sha256', $file['tmp_name']);
        $stmt = $pdo->prepare('SELECT COUNT(*) FROM audio_assets WHERE sha256 = ?');
        $stmt->execute([$sha]);
        expect((int) $stmt->fetchColumn() === 1, 'No second physical AudioAsset row');
    });
    run('Stage 7 rejects conflicting HTTP retry', function () use ($service, $fields, $file, $ownerHash): void {
        try {
            $service->upload(array_merge($fields, ['track_id' => '799003']), $file, $ownerHash);
            throw new RuntimeException('Conflicting retry accepted');
        } catch (DomainException $e) {
            expect($e->getMessage() === 'idempotency_conflict', 'Retry conflict');
        }
    });
    run('Stage 7 rejects fake, malformed, oversize and rights-free files', function () use ($service, $fields, $file, $ownerHash, $path, $pdo, $storage): void {
        $fake = $path . '.fake';
        file_put_contents($fake, str_repeat('not an mp3', 200));
        try {
            foreach ([
                [$fields, array_merge($file, ['tmp_name' => $fake, 'name' => 'fake.mp3', 'size' => filesize($fake)]), 'DomainException'],
                [array_merge($fields, ['declaration' => '0']), $file, 'DomainException'],
                [array_merge($fields, ['track_id' => '007']), $file, 'InvalidArgumentException'],
                [$fields, array_merge($file, ['error' => UPLOAD_ERR_PARTIAL]), 'InvalidArgumentException'],
                [$fields, array_merge($file, ['size' => 999]), 'InvalidArgumentException'],
            ] as [$f, $input, $expected]) {
                try {
                    $service->upload($f, $input, $ownerHash);
                    throw new RuntimeException('Unsafe upload accepted');
                } catch (Throwable $e) {
                    expect(get_class($e) === $expected, $expected . ' rejected');
                }
            }
            $limited = new UploadService($pdo, $storage, 1024, static fn (string $p): bool => is_file($p));
            try { $limited->upload($fields, $file, $ownerHash); throw new RuntimeException('Oversize accepted'); }
            catch (LengthException $e) { expect($e->getMessage() === 'upload_too_large', 'Oversize'); }
        } finally { unlink($fake); }
    });
    run('Stage 7 protected route disabled by default even with read token', function () use ($config): void {
        $config['owner_uploads_enabled'] = false;
        $config['owner_upload_token'] = str_repeat('x', 48);
        $app = new Application($config);
        expect($app->handle('POST', '/api/v1/uploads', [], ['Authorization' => 'Bearer ' . $config['owner_upload_token']])->status === 503, 'Default off');
    });
    run('Stage 7 owner-only API and rate limiter guard writes', function () use ($config, $pdo, $ownerHash): void {
        $config['owner_uploads_enabled'] = true;
        $config['owner_upload_token'] = str_repeat('owner-only-ci-token-', 3);
        $app = new Application($config);
        expect($app->handle('POST', '/api/v1/uploads', [], ['Authorization' => 'Bearer ' . $config['test_api_token']])->status === 401, 'Read token denied');
        expect($app->handle('POST', '/api/v1/uploads', [], ['Authorization' => 'Bearer ' . $config['owner_upload_token']],
            '', [], [])->status === 415, 'Multipart required');
        $limiter = new UploadRateLimiter($pdo);
        $who = hash('sha256', $ownerHash . bin2hex(random_bytes(4)));
        expect($limiter->check($who, 'upload', 2), 'First');
        expect($limiter->check($who, 'upload', 2), 'Second');
        expect(!$limiter->check($who, 'upload', 2), 'Third rate limited');
    });
    run('Stage 7 track requests are private and idempotent', function () use ($pdo, $ownerHash): void {
        $requests = new TrackRequestService($pdo);
        $params = ['service' => 'yandex', 'track_id' => '799009', 'artist' => 'CI', 'title' => 'fixture'];
        $first = $requests->submit($params, $ownerHash);
        $next = $requests->submit($params, $ownerHash);
        expect($first === $next && $first['status'] === 'pending', 'Same owner+Track returns existing');
    });
    fwrite(STDOUT, "CELIKOM Stage 7 isolated upload foundation passed.\n");
} finally {
    unlink($path);
}
