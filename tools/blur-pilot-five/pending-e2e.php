<?php

declare(strict_types=1);

/**
 * Isolated E2E for five pilot IDs using generated synthetic MP3 frames only.
 * MUST NEVER be run against production, or with real artist recordings.
 */

$root = dirname(__DIR__, 2);
require_once $root . '/server/bootstrap.php';

use Celikom\Application\UploadService;
use Celikom\Application\Mp3Inspector;
use Celikom\Application\ReplacementCatalogueService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Repositories\PdoCatalogRepository;
use Celikom\Storage\LocalStorageAdapter;

const PILOT_DB = 'celikom_test_blur_five';
const PILOT_BRANCH = 'feature/blur-pilot-five-20261108';

$config = require $root . '/server/config/app.php';
$storagePath = (string) $config['storage_path'];
if (getenv('CI') !== 'true' || getenv('GITHUB_REF_NAME') !== PILOT_BRANCH
    || $config['environment'] !== 'test' || $config['db_name'] !== PILOT_DB
    || !in_array((string) $config['db_host'], ['127.0.0.1', 'localhost'], true)
    || !str_starts_with($storagePath, '/tmp/celikom-blur-five-e2e/')) {
    throw new RuntimeException('refuse_non_disposable_environment');
}

$manifest = json_decode(file_get_contents(__DIR__ . '/pilot.json'), true, flags: JSON_THROW_ON_ERROR);
$tracks = $manifest['tracks'] ?? [];
if (!is_array($tracks) || count($tracks) !== 5 || count(array_unique(array_column($tracks, 'track_id'))) !== 5) {
    throw new RuntimeException('invalid_pilot_manifest');
}

$pdo = Connection::open($config);
(new MigrationRunner($pdo, $root . '/server/migrations'))->run();
$storage = new LocalStorageAdapter($storagePath);
$uploaderHash = hash('sha256', 'celikom-blur-five-synthetic-ci-only');
$service = new UploadService($pdo, $storage, 31457280, static fn (string $path): bool => is_file($path));
$catalogue = new PdoCatalogRepository($pdo);

$created = [];
$paths = [];
try {
    foreach ($tracks as $index => $entry) {
        $id = (string) $entry['track_id'];
        if (!preg_match('/^[1-9][0-9]{0,19}$/D', $id)) throw new RuntimeException('bad_id');
        // 100 MPEG1 Layer3 128 kbps 44.1 kHz frames, ~2612 ms.
        // Each file gets distinct generated payload and SHA; NOT the real track.
        $frame = hex2bin('fffb9064') . str_repeat(chr(65 + $index), 413);
        $path = tempnam(sys_get_temp_dir(), 'celikom-blur5-');
        if ($path === false) throw new RuntimeException('temp_unavailable');
        $paths[] = $path;
        if (file_put_contents($path, str_repeat($frame, 100)) !== 41700) {
            throw new RuntimeException('synthetic_fixture_failed');
        }
        $duration = (new Mp3Inspector())->durationMs($path);
        if ($duration === null || abs($duration - 2612) > 100) throw new RuntimeException('bad_synthetic_duration');

        $fields = [
            'service' => 'yandex', 'track_id' => $id, 'duration_ms' => (string) $duration,
            'artist' => (string) $entry['artist'], 'title' => (string) $entry['title'],
            'album' => '', 'declaration' => '1', // Owner-made synthetic test fixture only.
            'request_id' => sprintf('10000000-0000-4000-8000-%012d', $index + 1),
        ];
        $file = ['error' => UPLOAD_ERR_OK, 'tmp_name' => $path, 'name' => $id . '.mp3', 'size' => filesize($path)];
        $result = $service->upload($fields, $file, $uploaderHash);
        if ($result['status'] !== 'pending' || $result['duplicate'] || $result['replacement_id'] < 1) {
            throw new RuntimeException('pending_not_created');
        }
        $created[] = ['id' => $id, 'replacement_id' => $result['replacement_id']];
        if ($catalogue->findActive('yandex', $id) !== null) throw new RuntimeException('unexpected_publication');
        // Verify idempotency without a second row.
        $repeat = $service->upload($fields, $file, $uploaderHash);
        if ($repeat['status'] !== 'pending' || !$repeat['duplicate'] || $repeat['replacement_id'] !== $result['replacement_id']) {
            throw new RuntimeException('idempotency_failed');
        }
    }
    if (count($created) !== 5) throw new RuntimeException('wrong_created_count');
    $status = $pdo->query("SELECT status, is_active, COUNT(*) AS n FROM track_replacements GROUP BY status, is_active")->fetchAll(PDO::FETCH_ASSOC);
    if (count($status) !== 1 || $status[0]['status'] !== 'pending'
        || (int) $status[0]['is_active'] !== 0 || (int) $status[0]['n'] !== 5) {
        throw new RuntimeException('unexpected_mapping_status');
    }
    $count = (int) $pdo->query('SELECT COUNT(*) FROM tracks')->fetchColumn();
    $assets = (int) $pdo->query('SELECT COUNT(*) FROM audio_assets')->fetchColumn();
    $requests = (int) $pdo->query('SELECT COUNT(*) FROM track_requests')->fetchColumn();
    if ($count !== 5 || $assets !== 5 || $requests !== 0) throw new RuntimeException('unexpected_table_counts');
    $snapshot = (new ReplacementCatalogueService($pdo))->snapshot();
    if ($snapshot['total_tracks'] !== 0 || $snapshot['complete'] !== true) throw new RuntimeException('pending_exposed');
    $bad = ['service' => 'yandex', 'track_id' => '55555555', 'duration_ms' => '2612', 'artist' => 'synthetic',
        'title' => 'invalid declaration test', 'album' => '', 'declaration' => '0',
        'request_id' => '10000000-0000-4000-8000-000000000099'];
    try {
        $service->upload($bad, ['error' => UPLOAD_ERR_OK, 'tmp_name' => $paths[0], 'name' => 'a.mp3', 'size' => filesize($paths[0])], $uploaderHash);
        throw new RuntimeException('rights_gate_bypassed');
    } catch (DomainException $expected) {
        if ($expected->getMessage() !== 'rights_declaration_required') throw $expected;
    }
    $bad['declaration'] = '1';
    $bad['duration_ms'] = '5012';
    try {
        $service->upload($bad, ['error' => UPLOAD_ERR_OK, 'tmp_name' => $paths[0], 'name' => 'a.mp3', 'size' => filesize($paths[0])], $uploaderHash);
        throw new RuntimeException('duration_gate_bypassed');
    } catch (DomainException $expected) {
        if ($expected->getMessage() !== 'duration_mismatch') throw $expected;
    }
    if ((int) $pdo->query('SELECT COUNT(*) FROM tracks')->fetchColumn() !== 5) throw new RuntimeException('bad_data_persisted');
    echo json_encode(['status' => 'PASS', 'mode' => 'CI_MYSQL_SYNTHETIC_ONLY',
        'pilot_track_ids' => array_column($tracks, 'track_id'),
        'pending_created' => 5, 'active' => 0, 'approved' => 0,
        'catalogue_visible' => $snapshot['total_tracks'], 'unique_assets' => 5,
        'idempotency' => 'PASS', 'rights_gate' => 'PASS', 'duration_gate' => 'PASS',
        'production_writes' => 0, 'copyrighted_audio_used' => false],
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR) . "\n";
} finally {
    foreach ($paths as $path) if (is_file($path)) unlink($path);
}