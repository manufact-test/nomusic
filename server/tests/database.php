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
    run('Stage 6 guarded activation rejects stale expected active mapping', function () use ($pdo, $catalog, $storage): void {
        $manager = new LibraryManagementService($pdo, $storage);
        $track = $manager->addTrack('yandex', '600004', 1000);
        $asset = (int) $pdo->query('SELECT id FROM audio_assets ORDER BY id LIMIT 1')->fetchColumn();
        $id = $manager->link($track, $asset);
        $manager->approve($id, true);
        try {
            $manager->activate($id, true, 888888);
            throw new RuntimeException('Accepted stale activation');
        } catch (InvalidArgumentException $error) {
            expect($error->getMessage() === 'library_expected_active_mismatch', 'Expected mapping enforced');
        }
        expect($catalog->findActive('yandex', '600004') === null, 'No mutation on expected mismatch');
        $manager->activate($id, true, 0);
        expect((int) $catalog->findActive('yandex', '600004')['replacement_id'] === $id, 'No-current guard accepted');
        try {
            $manager->disable($id, true, 0);
            throw new RuntimeException('Accepted stale disable');
        } catch (InvalidArgumentException $error) {
            expect($error->getMessage() === 'library_expected_active_mismatch', 'Disable expected active enforced');
        }
        expect($catalog->findActive('yandex', '600004') !== null, 'Unchanged after denied disable');
        $manager->disable($id, true, $id);
        expect($catalog->findActive('yandex', '600004') === null, 'Correct guard permits disable');
    });
    run('Stage 6 CLI: strict arguments and private staging path guards', function () use ($directory): void {
        require_once dirname(__DIR__) . '/bin/library-cli.php';
        $track = celikomLibraryParse('add-track', ['cli', '--track-id=1234', '--duration-ms=1000', '--title=Fixture']);
        expect($track['track-id'] === '1234' && $track['title'] === 'Fixture', 'Valid Track arguments');
        $approve = celikomLibraryParse('approve', ['cli', '--replacement-id=15', '--confirm-reviewed']);
        expect($approve['confirm-reviewed'] === true, 'Explicit confirmation accepted');
        foreach ([
            ['add-track', ['cli', '--track-id=1234']],
            ['add-track', ['cli', '--track-id=0', '--duration-ms=1000']],
            ['add-track', ['cli', '--track-id=1234', '--duration-ms=1000', '--unknown=1']],
            ['add-track', ['cli', '--track-id=1234', '--track-id=1234', '--duration-ms=1000']],
            ['add-asset', ['cli', '--staging-file=../outside.wav', '--duration-ms=1000', '--confirm-reviewed']],
            ['add-asset', ['cli', '--staging-file=fixture.wav', '--duration-ms=1000']],
            ['approve', ['cli', '--replacement-id=15']],
            ['approve', ['cli', '--replacement-id=15', '--confirm-reviewed=false']],
            ['activate', ['cli', '--replacement-id=15']],
            ['disable', ['cli', '--replacement-id=15']],
            ['link', ['cli', '--track-db-id=-1', '--asset-id=1']],
        ] as [$operation, $arguments]) {
            try {
                celikomLibraryParse($operation, $arguments);
                throw new RuntimeException('Unsafe CLI accepted');
            } catch (InvalidArgumentException) {
                // Expected: no credentials/database/filesystem have been accessed.
            }
        }
        $staging = dirname($directory) . '/staging';
        if (!is_dir($staging)) {
            mkdir($staging, 0700, true);
        }
        $good = $staging . '/stage6-fixture.wav';
        file_put_contents($good, 'safe fixture');
        $link = $staging . '/stage6-link.wav';
        symlink($good, $link);
        try {
            expect(celikomLibraryStagedFile($directory, 'stage6-fixture.wav') === realpath($good), 'Private file accepted');
            foreach (['stage6-link.wav', '../fixture.wav', '.hidden.wav'] as $name) {
                try {
                    celikomLibraryStagedFile($directory, $name);
                    throw new RuntimeException('Unsafe staging file accepted');
                } catch (InvalidArgumentException) {
                    // No symlinks or traversal outside shared staging.
                }
            }
        } finally {
            unlink($link);
            unlink($good);
        }
    });
    run('Stage 6.6: two isolated API installations stream one shared asset by distinct signed mapping IDs', function () use ($config, $pdo, $storage, $wave): void {
        $manager = new LibraryManagementService($pdo, $storage);
        $assetId = (int) $pdo->query('SELECT id FROM audio_assets ORDER BY id LIMIT 1')->fetchColumn();
        expect($assetId > 0, 'Shared fixture AudioAsset exists');
        $tracks = [];
        foreach (['600010', '600011'] as $serviceId) {
            $trackId = $manager->addTrack('yandex', $serviceId, 1000);
            $replacementId = $manager->link($trackId, $assetId);
            $manager->approve($replacementId, true);
            $manager->activate($replacementId, true, 0);
            $tracks[$serviceId] = $replacementId;
        }
        expect($tracks['600010'] !== $tracks['600011'], 'Distinct TrackReplacement IDs');
        $statement = $pdo->prepare('SELECT COUNT(DISTINCT audio_asset_id) FROM track_replacements WHERE id IN (?, ?)');
        $statement->execute([$tracks['600010'], $tracks['600011']]);
        expect((int) $statement->fetchColumn() === 1, 'One physical shared AudioAsset');

        $appConfig = $config;
        $appConfig['api_enabled'] = true;
        $appConfig['analytics_enabled'] = false;
        $appConfig['test_api_token'] = str_repeat('stage6-owner-test-', 3);
        $appConfig['audio_signing_key'] = str_repeat('stage6-test-signing-', 3);
        $appConfig['audio_token_ttl'] = 600;
        $auth = ['Authorization' => 'Bearer ' . $appConfig['test_api_token']];
        $one = new Application($appConfig, new PdoCatalogRepository(Connection::open($config)), $storage);
        $two = new Application($appConfig, new PdoCatalogRepository(Connection::open($config)), $storage);
        foreach ([['600010', $tracks['600010'], $one], ['600011', $tracks['600011'], $two]] as [$track, $replacement, $app]) {
            $response = $app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => $track], $auth);
            expect($response->status === 200, 'Authenticated resolve status');
            $data = json_decode($response->body, true, flags: JSON_THROW_ON_ERROR);
            expect($data['found'] === true && $data['replacement_id'] === $replacement, 'Only exact ID resolves');
            expect(!str_contains($response->body, 'storage_key') && !str_contains($response->body, '/shared/'),
                'No private file name or private path returned');
            $route = parse_url($data['audio_url'], PHP_URL_PATH);
            parse_str((string) parse_url($data['audio_url'], PHP_URL_QUERY), $query);
            expect($route === '/api/v1/audio/' . $replacement, 'Version-signed private HTTP API route');
            $partial = $app->handle('GET', $route, $query, [
                'Range' => 'bytes=16-39', 'Origin' => 'https://music.yandex.ru',
            ]);
            expect($partial->status === 206 && bytes($partial) === substr($wave, 16, 24),
                'Shared WAV asset returns byte-exact 206 in both installations');
            expect($partial->headers['Content-Range'] === 'bytes 16-39/' . strlen($wave),
                'RFC 9110 Content-Range and exact byte count');
            expect($partial->headers['Cache-Control'] === 'private, no-store'
                && $partial->headers['Access-Control-Allow-Origin'] === 'https://music.yandex.ru',
                'Private HTTP caching and strict CORS');
            $head = $app->handle('HEAD', $route, $query, ['Range' => 'bytes=16-39']);
            expect($head->status === 200 && bytes($head) === ''
                && $head->headers['Content-Length'] === (string) strlen($wave),
                'HEAD ignores Range and never streams media');
            $bad = $app->handle('GET', $route, $query, ['Range' => 'bytes=999999-']);
            expect($bad->status === 416
                && $bad->headers['Content-Range'] === 'bytes */' . strlen($wave),
                '416 for unsatisfiable range');
            $blocked = $app->handle('GET', $route, $query, ['Range' => 'bytes=0-3', 'Origin' => 'https://evil.example']);
            expect($blocked->status === 206 && !isset($blocked->headers['Access-Control-Allow-Origin']),
                'Unknown origin never obtains CORS permission');
            expect($app->handle('GET', $route, ['expires' => $query['expires'], 'token' => str_repeat('f', 64)])->status === 403,
                'Signed URL cannot be forged');
            expect($app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => $track])->status === 401,
                'Resolve requires token, even for already approved ID');
        }

        $unknown = $one->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => '888001'], $auth);
        expect(json_decode($unknown->body, true, flags: JSON_THROW_ON_ERROR)['found'] === false,
            'Unmapped exact ID leaves original available');
        $manager->disable($tracks['600010'], true, $tracks['600010']);
        expect(json_decode($one->handle('GET', '/api/v1/resolve',
            ['service' => 'yandex', 'track_id' => '600010'], $auth)->body, true, flags: JSON_THROW_ON_ERROR)['found'] === false,
            'Disabling one shared mapping causes only that Track to fall back');
        expect($one->handle('GET', '/api/v1/audio/' . $tracks['600010'], ['expires' => '1', 'token' => str_repeat('f', 64)])->status === 404,
            'Disabled mapping cannot stream even with previously issued URL');
        expect(json_decode($two->handle('GET', '/api/v1/resolve',
            ['service' => 'yandex', 'track_id' => '600011'], $auth)->body, true, flags: JSON_THROW_ON_ERROR)['found'] === true,
            'Other Track remains approved and playable');
    });
    run('Stage 6.6: simultaneous editors serialize on Track lock and stale activation refuses change', function () use ($config, $pdo, $catalog, $storage): void {
        $manager = new LibraryManagementService($pdo, $storage);
        $trackId = $manager->addTrack('yandex', '600012', 1000);
        $assetIds = $pdo->query('SELECT id FROM audio_assets ORDER BY id LIMIT 2')->fetchAll(PDO::FETCH_COLUMN);
        expect(count($assetIds) === 2, 'Two independently reviewed fixture assets');
        $previous = $manager->link($trackId, (int) $assetIds[0]);
        $next = $manager->link($trackId, (int) $assetIds[1]);
        $manager->approve($previous, true);
        $manager->approve($next, true);
        $manager->activate($previous, true, 0);
        $secondConnection = Connection::open($config);
        $secondConnection->exec('SET SESSION innodb_lock_wait_timeout = 1');
        $secondEditor = new LibraryManagementService($secondConnection, $storage);

        $pdo->beginTransaction();
        try {
            $lock = $pdo->prepare('SELECT id FROM tracks WHERE id = ? FOR UPDATE');
            $lock->execute([$trackId]);
            expect($lock->fetchColumn() !== false, 'First editor holds Track row');
            try {
                $secondEditor->activate($next, true, $previous);
                throw new RuntimeException('Second editor bypassed the Track row lock');
            } catch (PDOException $error) {
                expect((int) ($error->errorInfo[1] ?? 0) === 1205,
                    'Competing connection times out on InnoDB row lock, without committing');
            }
            expect((int) $catalog->findActive('yandex', '600012')['replacement_id'] === $previous,
                'Timed-out write has not changed active mapping');
        } finally {
            $pdo->rollBack();
        }
        $secondEditor->activate($next, true, $previous);
        expect((int) $catalog->findActive('yandex', '600012')['replacement_id'] === $next,
            'Second editor succeeds after Track lock released');
        try {
            $manager->activate($previous, true, $previous);
            throw new RuntimeException('Accepted stale owner activation request');
        } catch (InvalidArgumentException $error) {
            expect($error->getMessage() === 'library_expected_active_mismatch', 'Stale compare-and-swap rejected');
        }
        expect((int) $catalog->findActive('yandex', '600012')['replacement_id'] === $next,
            'Stale request leaves approved mapping intact');
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
