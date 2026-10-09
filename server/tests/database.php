<?php

declare(strict_types=1);

require __DIR__ . '/smoke.php';

use Celikom\Application;
use Celikom\Application\TestAudioImporter;
use Celikom\Application\AudioTokenService;
use Celikom\Application\ResolveService;
use Celikom\Application\LibraryManagementService;
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
    run('Stage 6: two exact IDs share one AudioAsset and resolve independently', function () use ($pdo, $catalog, $storage, $id): void {
        $statement = $pdo->query("SELECT t.service_track_id, r.id AS replacement_id, r.audio_asset_id, a.storage_key
            FROM tracks t JOIN track_replacements r ON r.track_id = t.id
            JOIN audio_assets a ON a.id = r.audio_asset_id
            WHERE t.service = 'yandex' AND t.service_track_id IN ('1944599', '999')
                AND r.status = 'approved' AND r.is_active = 1
            ORDER BY t.service_track_id");
        $rows = $statement->fetchAll(PDO::FETCH_ASSOC);
        expect(count($rows) === 2, 'Both exact IDs mapped');
        expect($rows[0]['audio_asset_id'] === $rows[1]['audio_asset_id'], 'Same AudioAsset');
        expect($rows[0]['storage_key'] === $rows[1]['storage_key'], 'Same storage key');
        expect((int) $rows[0]['replacement_id'] !== (int) $rows[1]['replacement_id'], 'Separate TrackReplacement IDs');
        expect((int) $pdo->query('SELECT COUNT(*) FROM audio_assets')->fetchColumn() === 1, 'One stored AudioAsset');
        $tokens = new AudioTokenService(str_repeat('stage6-test-signing-', 3));
        $first = new ResolveService($catalog, $storage, $tokens);
        $second = new ResolveService($catalog, $storage, $tokens);
        $a = $first->resolve('yandex', '1944599');
        $b = $second->resolve('yandex', '999');
        expect($a['found'] === true && $b['found'] === true, 'Independent lookups');
        expect($a['replacement_id'] === $id && $a['replacement_id'] !== $b['replacement_id'], 'Mapping identity');
        $unknown = $first->resolve('yandex', '888888');
        expect($unknown['found'] === false && $unknown['cache_ttl_seconds'] < $a['cache_ttl_seconds'], 'Short negative TTL');
        expect(str_starts_with($a['audio_url'], '/api/v1/audio/'), 'Audio path is API-only');
        expect(!str_contains(json_encode([$a, $b], JSON_THROW_ON_ERROR), $rows[0]['storage_key']), 'No private key exposed');
    });
    run('Stage 6: candidate stays private until explicitly selected; other Track stays intact', function () use ($pdo, $catalog, $id): void {
        $other = $catalog->findActive('yandex', '999');
        expect($catalog->findActive('yandex', '1944599') !== null && $other !== null, 'Precondition');
        $insert = $pdo->prepare("INSERT INTO track_replacements (track_id, audio_asset_id, status, is_active)
            SELECT track_id, audio_asset_id, 'pending', 0 FROM track_replacements WHERE id = ?");
        $insert->execute([$id]);
        $candidate = (int) $pdo->lastInsertId();
        expect($candidate > 0 && $catalog->findByReplacement($candidate) === null, 'Pending not streamable');
        expect((int) $catalog->findActive('yandex', '1944599')['replacement_id'] === $id, 'Pending cannot override');
        $pdo->prepare("UPDATE track_replacements SET status = 'approved', approved_at = CURRENT_TIMESTAMP(6)
            WHERE id = ?")->execute([$candidate]);
        expect($catalog->findByReplacement($candidate) === null, 'Inactive approved not streamable');
        $pdo->beginTransaction();
        try {
            // Disposable fixture transition only: a real management service comes in 6.2.
            $lock = $pdo->prepare('SELECT id FROM tracks WHERE service = ? AND service_track_id = ? FOR UPDATE');
            $lock->execute(['yandex', '1944599']);
            expect($lock->fetchColumn() !== false, 'Track locked');
            $pdo->prepare('UPDATE track_replacements SET is_active = 0 WHERE id = ?')->execute([$id]);
            $pdo->prepare('UPDATE track_replacements SET is_active = 1 WHERE id = ?')->execute([$candidate]);
            $pdo->commit();
        } catch (Throwable $error) {
            $pdo->rollBack();
            throw $error;
        }
        expect($catalog->findByReplacement($id) === null, 'Old mapping cannot stream');
        expect((int) $catalog->findActive('yandex', '1944599')['replacement_id'] === $candidate, 'Explicit selection');
        expect((int) $catalog->findActive('yandex', '999')['replacement_id'] === (int) $other['replacement_id'], 'Other Track unchanged');
        expect((int) $pdo->query('SELECT COUNT(*) FROM audio_assets')->fetchColumn() === 1, 'No extra file');
    });
    run('Stage 6 manager: owner-reviewed asset registration, pending link and explicit approval', function () use ($pdo, $catalog, $storage, $file): void {
        $manager = new LibraryManagementService($pdo, $storage);
        $track = $manager->addTrack('yandex', '600001', 1000, ['artist' => 'CI fixture']);
        expect($manager->addTrack('yandex', '600001', 1000) === $track, 'Idempotent Track');
        try {
            $manager->addReviewedAsset($file, 1000, false);
            throw new RuntimeException('Unreviewed fixture accepted');
        } catch (InvalidArgumentException $error) {
            expect($error->getMessage() === 'owner_review_required', 'Owner-reviewed flag required');
        }
        $asset = $manager->addReviewedAsset($file, 1000, true);
        expect($manager->addReviewedAsset($file, 1000, true) === $asset, 'Exact hash dedup');
        expect((int) $pdo->query('SELECT COUNT(*) FROM audio_assets')->fetchColumn() === 1, 'Existing asset reused');
        $link = $manager->link($track, $asset);
        expect($manager->link($track, $asset) === $link, 'Link idempotent');
        expect($catalog->findActive('yandex', '600001') === null, 'Pending never published');
        expect($catalog->findByReplacement($link) === null, 'Pending audio denied');
        try {
            $manager->activate($link, true);
            throw new RuntimeException('Pending activated');
        } catch (InvalidArgumentException $error) {
            expect($error->getMessage() === 'library_candidate_not_approved', 'Approval required');
        }
        try {
            $manager->approve($link, false);
            throw new RuntimeException('Approved without owner');
        } catch (InvalidArgumentException $error) {
            expect($error->getMessage() === 'owner_review_required', 'Owner consent required');
        }
        $manager->approve($link, true);
        expect($catalog->findActive('yandex', '600001') === null, 'Approved but inactive');
        try {
            $manager->activate($link, false);
            throw new RuntimeException('Activated without owner');
        } catch (InvalidArgumentException $error) {
            expect($error->getMessage() === 'owner_activation_required', 'Explicit activation required');
        }
        $manager->activate($link, true);
        $selected = $catalog->findActive('yandex', '600001');
        expect((int) $selected['replacement_id'] === $link, 'Approved active selected');
        $version = (int) $selected['version'];
        $manager->activate($link, true);
        expect((int) $catalog->findActive('yandex', '600001')['version'] === $version, 'Active retry does not bump version');
    });
    run('Stage 6 manager: switching a candidate revokes old signed version and disable fails open', function () use ($pdo, $catalog, $storage, $wave): void {
        $manager = new LibraryManagementService($pdo, $storage);
        $track = $manager->addTrack('yandex', '600001', 1000);
        $first = $catalog->findActive('yandex', '600001');
        expect($first !== null, 'First approved mapping available');
        $oldId = (int) $first['replacement_id'];
        $oldVersion = (int) $first['version'];
        $otherFile = sys_get_temp_dir() . '/celikom-stage6-fixture-' . bin2hex(random_bytes(8)) . '.wav';
        file_put_contents($otherFile, substr($wave, 0, -8000) . str_repeat("\x81", 8000));
        try {
            $otherAsset = $manager->addReviewedAsset($otherFile, 1000, true);
            $candidate = $manager->link($track, $otherAsset);
            expect($catalog->findActive('yandex', '600001')['replacement_id'] == $oldId, 'New candidate cannot override');
            $manager->approve($candidate, true);
            $manager->activate($candidate, true);
            expect((int) $catalog->findActive('yandex', '600001')['replacement_id'] === $candidate, 'New approved mapping active');
            expect($catalog->findByReplacement($oldId) === null, 'Old mapping revoked while inactive');
            $manager->activate($oldId, true);
            $reactivated = $catalog->findActive('yandex', '600001');
            expect((int) $reactivated['replacement_id'] === $oldId, 'Can restore old approved mapping');
            expect((int) $reactivated['version'] > $oldVersion, 'Reactivation bumps token-bound version');
            $tokens = new AudioTokenService(str_repeat('stage6-test-signing-', 3));
            $expiry = time() + 300;
            $oldSignature = $tokens->sign($oldId, $oldVersion, $expiry);
            expect(!$tokens->valid($oldId, (int) $reactivated['version'], (string) $expiry, $oldSignature), 'Old signed URL invalid');
            $manager->disable($oldId, true);
            expect($catalog->findActive('yandex', '600001') === null, 'Disable immediately fails open');
            $manager->disable($oldId, true);
            expect($catalog->findByReplacement($oldId) === null, 'Disabled mapping never streams');
        } finally {
            unlink($otherFile);
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
