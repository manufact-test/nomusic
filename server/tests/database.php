<?php

declare(strict_types=1);

require __DIR__ . '/smoke.php';

use Celikom\Application;
use Celikom\Application\TestAudioImporter;
use Celikom\Analytics\AnalyticsEventService;
use Celikom\Analytics\AnalyticsQueryService;
use Celikom\Analytics\PdoEventRepository;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Repositories\PdoCatalogRepository;
use Celikom\Storage\LocalStorageAdapter;

$config = require dirname(__DIR__) . '/config/app.php';
if (!$config['db_name']) {
    fwrite(STDOUT, "MySQL integration deferred: configure a celikom_test database.\n");
    if (getenv('CI')) {
        throw new RuntimeException('CI must run real MySQL integration.');
    }
    exit(0);
}
if (!str_starts_with($config['db_name'], 'celikom_test')) {
    throw new RuntimeException('Tests require a disposable celikom_test* database.');
}
$pdo = Connection::open($config);
$runner = new MigrationRunner($pdo, dirname(__DIR__) . '/migrations');
run('MySQL migrations apply and rerun without changes', function () use ($runner): void {
    $runner->run();
    expect($runner->run() === [], 'Migration retry');
});
foreach (['track_replacements', 'audio_assets', 'tracks', 'analytics_events', 'analytics_daily_aggregates'] as $table) {
    $pdo->exec('DELETE FROM ' . $table);
}
$directory = $config['storage_path'];
$storage = new LocalStorageAdapter($directory);
$file = sys_get_temp_dir() . '/celikom-test-audio-' . bin2hex(random_bytes(8)) . '.wav';
$samples = str_repeat("\x80", 8000);
$wave = 'RIFF' . pack('V', 36 + strlen($samples)) . 'WAVEfmt ' . pack('VvvVVvv', 16, 1, 1, 8000, 8000, 1, 8) . 'data' . pack('V', strlen($samples)) . $samples;
file_put_contents($file, $wave);
$importer = new TestAudioImporter($pdo, $storage);
$catalog = new PdoCatalogRepository($pdo);
try {
    $id = $importer->import($file, 'yandex', '1944599', 1000);
    run('reviewed fixture import is idempotent and one asset can map to several IDs', function () use ($pdo, $file, $importer, $id): void {
        expect($importer->import($file, 'yandex', '1944599', 1000) === $id, 'Repeated import');
        $importer->import($file, 'yandex', '999', 1000);
        expect((int) $pdo->query('SELECT COUNT(*) FROM audio_assets')->fetchColumn() === 1, 'Shared AudioAsset');
    });
    run('pending/rejected/disabled/inactive mappings do not resolve', function () use ($pdo, $catalog, $id): void {
        foreach ([['pending', 0], ['rejected', 0], ['disabled', 0], ['approved', 0]] as [$status, $active]) {
            $statement = $pdo->prepare('UPDATE track_replacements SET status = ?, is_active = ? WHERE id = ?');
            $statement->execute([$status, $active, $id]);
            expect($catalog->findActive('yandex', '1944599') === null, 'Not publicly active');
        }
        $statement = $pdo->prepare("UPDATE track_replacements SET status = 'approved', is_active = 1 WHERE id = ?");
        $statement->execute([$id]);
        expect($catalog->findActive('yandex', '1944599') !== null, 'Approved active');
    });
    run('MySQL enforces one active approved replacement per exact track', function () use ($pdo, $id): void {
        try {
            $statement = $pdo->prepare("INSERT INTO track_replacements (track_id, audio_asset_id, status, is_active) SELECT track_id, audio_asset_id, 'approved', 1 FROM track_replacements WHERE id = ?");
            $statement->execute([$id]);
            throw new RuntimeException('Multiple active replacements accepted');
        } catch (PDOException $error) {
            expect(($error->errorInfo[1] ?? null) === 1062, 'Unique mapping constraint');
        }
    });
    run('repository uses exact prepared service identity', function () use ($catalog): void {
        expect($catalog->findActive('yandex', "1944599' OR 1=1") === null, 'SQL injection rejected');
        expect($catalog->findActive('other', '1944599') === null, 'Exact service');
    });
    $analytics = new AnalyticsEventService(new PdoEventRepository($pdo), str_repeat('database-privacy-', 3));
    $event = ['schema_version' => 1, 'installation_id' => '00000000-0000-4000-8000-000000000001', 'client_version' => '0.4.0', 'platform' => 'chromium', 'events' => [[
        'event_id' => '00000000-0000-4000-8000-000000000010', 'event_name' => 'celikom_started', 'occurred_at' => gmdate('Y-m-d\TH:i:s\Z'), 'properties' => [],
    ]]];
    run('MySQL analytics retry and daily aggregation never double count', function () use ($analytics, $event, $pdo): void {
        expect($analytics->batch($event)['results'][0]['status'] === 'accepted', 'First batch');
        expect($analytics->batch($event)['results'][0]['status'] === 'duplicate', 'Retried batch');
        $query = new AnalyticsQueryService($pdo);
        $query->aggregateDay(gmdate('Y-m-d'));
        $query->aggregateDay(gmdate('Y-m-d'));
        $row = $pdo->query('SELECT event_count, installation_count FROM analytics_daily_aggregates')->fetch();
        expect((int) $row['event_count'] === 1 && (int) $row['installation_count'] === 1, 'Idempotent aggregates');
    });
    run('analytics raw retention is configurable', function () use ($pdo): void {
        $pdo->exec("UPDATE analytics_events SET occurred_at = '2020-01-01 00:00:00'");
        expect((new AnalyticsQueryService($pdo))->purge(30) === 1, 'Retention');
    });
    fwrite(STDOUT, "CELIKOM MySQL integration passed; approved WAV fixture is ready for HTTP tests.\n");
} finally {
    unlink($file);
}
