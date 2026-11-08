<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';

function ensure(bool $condition, string $reason): void
{
    if (!$condition) {
        throw new \RuntimeException($reason);
    }
}

if (!in_array('sqlite', \PDO::getAvailableDrivers(), true)) {
    fwrite(STDERR, "SQLite driver required for replacement-catalogue test\n");
    exit(2);
}
$pdo = new \PDO('sqlite::memory:');
$pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
$pdo->exec('CREATE TABLE tracks (
    id INTEGER PRIMARY KEY, service TEXT, service_track_id TEXT, title TEXT,
    artist TEXT, album TEXT, duration_ms INTEGER)');
$pdo->exec('CREATE TABLE track_replacements (
    id INTEGER PRIMARY KEY, track_id INTEGER, status TEXT,
    is_active INTEGER, disabled_at TEXT)');
$pdo->exec("INSERT INTO tracks VALUES
 (1,'yandex','118910020','Мне нужна любовь','Татем','Мне нужна любовь',102380),
 (2,'yandex','39949113','Дым','Лёша Свик','',170000),
 (3,'yandex','123','Не одобрена','Автор','',120000),
 (4,'spotify','90000','Не Яндекс','Автор','',120000),
 (5,'yandex','8000','Отключена','Автор','',120000)");
$pdo->exec("INSERT INTO track_replacements VALUES
 (1,1,'approved',1,NULL), (2,1,'approved',1,NULL),
 (3,2,'approved',1,NULL), (4,3,'pending',1,NULL),
 (5,4,'approved',1,NULL), (6,5,'approved',0,NULL)");
$service = new \Celikom\Application\ReplacementCatalogueService($pdo);
$one = $service->snapshot();
ensure($one['schema'] === 1 && $one['complete'] === true, 'Invalid snapshot contract');
ensure($one['total_tracks'] === 2, 'Only two approved active Yandex songs; no duplicate row');
ensure(array_column($one['tracks'], 'track_id') === ['118910020','39949113'], 'Wrong ids/order');
ensure($one['tracks'][0]['replacement_available'] === true, 'Approved status missing');
ensure(!isset($one['tracks'][0]['storage_key']), 'Private storage must not leak');
ensure(!isset($one['tracks'][0]['user_id']), 'Owner identity must not leak');
// An approval immediately changes the next snapshot. No APK build, cron or
// developer intervention is necessary.
$pdo->exec("UPDATE track_replacements SET status='approved' WHERE id=4");
$two = $service->snapshot();
ensure($two['total_tracks'] === 3, 'New approval must appear on next request');
// Revocation immediately removes a track.
$pdo->exec("UPDATE track_replacements SET disabled_at='2026-11-08' WHERE track_id=1");
$three = $service->snapshot();
ensure($three['total_tracks'] === 2 && $three['tracks'][0]['track_id'] === '39949113', 'Revoked track exposed');
// Bad data must fail closed instead of shipping a partial snapshot.
$pdo->exec("UPDATE tracks SET title='' WHERE id=2");
try {
    $service->snapshot();
    throw new \RuntimeException('Invalid row was accepted');
} catch (\RuntimeException $error) {
    ensure($error->getMessage() === 'catalogue_invalid_row', 'Wrong validation error');
}
echo "PASS: automatic live approved catalogue; no duplicates, no pending/disabled/other-service tracks; new approvals and revocations; no secrets\n";
