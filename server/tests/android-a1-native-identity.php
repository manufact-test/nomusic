<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';

use Celikom\Admin\NativeIdentityService;
use Celikom\Application\AudioTokenService;
use Celikom\Application\ResolveService;
use Celikom\Repositories\PdoCatalogRepository;
use Celikom\Storage\StorageAdapter;

function nativeEnsure(bool $ok, string $message): void
{
    if (!$ok) throw new RuntimeException($message);
}

if (!in_array('sqlite', PDO::getAvailableDrivers(), true)) {
    fwrite(STDERR, "SQLite driver required for Android A1 native identity test\n");
    exit(2);
}

$pdo = new PDO('sqlite::memory:');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->exec('CREATE TABLE tracks (
    id INTEGER PRIMARY KEY, service TEXT NOT NULL, service_track_id TEXT NOT NULL,
    service_album_id TEXT NULL, service_edition_id TEXT NULL)');
$pdo->exec('CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER NOT NULL, action TEXT NOT NULL,
    entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL, reason TEXT NOT NULL,
    before_json TEXT NULL, after_json TEXT NULL)');
$pdo->exec('CREATE TABLE track_replacements (
    id INTEGER PRIMARY KEY, track_id INTEGER NOT NULL, audio_asset_id INTEGER NOT NULL,
    status TEXT NOT NULL, is_active INTEGER NOT NULL, disabled_at TEXT NULL,
    version INTEGER NOT NULL, gain_db REAL NOT NULL)');
$pdo->exec('CREATE TABLE audio_assets (
    id INTEGER PRIMARY KEY, storage_driver TEXT NOT NULL, storage_key TEXT NOT NULL,
    sha256 TEXT NOT NULL, mime_type TEXT NOT NULL, size_bytes INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL)');
$pdo->exec("INSERT INTO tracks VALUES (1,'yandex','123',NULL,NULL),(2,'spotify','456',NULL,NULL)");
$pdo->exec("INSERT INTO audio_assets VALUES (9,'local','fixture-audio','".str_repeat('a',64)."','audio/mpeg',4096,180000)");
$pdo->exec("INSERT INTO track_replacements VALUES (42,1,9,'approved',1,NULL,3,0.0)");

$identity = new NativeIdentityService($pdo);
nativeEnsure($identity->update(7,1,'123','77','studio-edition-v1'), 'owner identity must save');
$row = $pdo->query('SELECT service_album_id,service_edition_id FROM tracks WHERE id=1')->fetch(PDO::FETCH_ASSOC);
nativeEnsure($row['service_album_id'] === '77' && $row['service_edition_id'] === 'studio-edition-v1',
    'exact opaque identity must round-trip');
nativeEnsure(!$identity->update(7,1,'123','77','studio-edition-v1'), 'same identity must be idempotent');
nativeEnsure((int)$pdo->query('SELECT COUNT(*) FROM audit_log')->fetchColumn() === 1,
    'only actual identity change is audited');

try {
    $identity->update(7,1,'123','77',null);
    throw new RuntimeException('partial identity accepted');
} catch (InvalidArgumentException $e) {
    nativeEnsure($e->getMessage() === 'invalid_native_identity', 'wrong partial identity error');
}
try {
    $identity->update(7,1,'999','77','studio-edition-v1');
    throw new RuntimeException('stale track accepted');
} catch (DomainException $e) {
    nativeEnsure($e->getMessage() === 'stale_native_identity', 'wrong stale identity error');
}
try {
    $identity->update(7,1,'123','77',"bad\x00edition");
    throw new RuntimeException('control character accepted');
} catch (InvalidArgumentException $e) {
    nativeEnsure($e->getMessage() === 'invalid_native_identity', 'wrong control character error');
}
try {
    $identity->update(7,1,'123','0','edition');
    throw new RuntimeException('invalid album ID accepted');
} catch (InvalidArgumentException $e) {
    nativeEnsure($e->getMessage() === 'invalid_native_identity', 'wrong album ID error');
}
try {
    $identity->update(7,2,'456','77','edition');
    throw new RuntimeException('non-Yandex identity accepted');
} catch (DomainException $e) {
    nativeEnsure($e->getMessage() === 'stale_native_identity', 'wrong service guard error');
}

$storage = new class implements StorageAdapter {
    public function put(string $key, mixed $source): void { throw new LogicException('write forbidden'); }
    public function openStream(string $key): mixed { throw new LogicException('read stream not required'); }
    public function exists(string $key): bool { return $key === 'fixture-audio'; }
    public function delete(string $key): void { throw new LogicException('delete forbidden'); }
    public function move(string $from, string $to): void { throw new LogicException('move forbidden'); }
    public function getSize(string $key): int { return 4096; }
    public function getMimeType(string $key): string { return 'audio/mpeg'; }
};
$catalog = new PdoCatalogRepository($pdo);
$tokens = new AudioTokenService(str_repeat('k',64),600);
$resolve = new ResolveService($catalog,$storage,$tokens,120,15);
$access = [
    'session_id'=>17,
    'refresh_expires_at'=>'2999-01-01 00:00:00',
    'valid_until'=>'2999-01-01 00:00:00',
];
$grant = $resolve->resolve('yandex','123',$access);
nativeEnsure(($grant['found'] ?? false) === true, 'active approved track must resolve');
nativeEnsure($grant['track_id'] === '123' && $grant['approved'] === true && $grant['entitled'] === true,
    'resolve must attest exact track, active approval and authenticated entitlement');
nativeEnsure($grant['album_id'] === '77' && $grant['edition_id'] === 'studio-edition-v1',
    'resolve must return exact native identity');
nativeEnsure(str_contains($grant['audio_url'],'sid=17'), 'entitled resolve must remain session-bound');

$privateTestGrant = $resolve->resolve('yandex','123',null);
nativeEnsure($privateTestGrant['entitled'] === false,
    'private API-token test access must never claim user entitlement');
nativeEnsure($privateTestGrant['approved'] === true, 'active mapping approval remains explicit');

$identity->update(7,1,'123',null,null);
$unverified = $resolve->resolve('yandex','123',$access);
nativeEnsure($unverified['album_id'] === null && $unverified['edition_id'] === null,
    'unverified identity must remain null, never fabricated');
nativeEnsure($unverified['approved'] === true && $unverified['entitled'] === true,
    'approval and entitlement remain distinct from missing identity');

echo "PASS: owner-only exact native identity validation, audit, clear, active approval, user entitlement, private-token denial, and fail-closed null mapping\n";
