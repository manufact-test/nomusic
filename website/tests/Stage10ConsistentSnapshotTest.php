<?php
declare(strict_types=1);
/**
 * Stage 10 CI-only coordinated snapshot protocol.
 * Proves that a second MySQL connection can commit an editorial change
 * BETWEEN exports while both authenticated artifacts retain one old MVCC view.
 * Does not touch Hostinger or public website routes.
 */
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsBackup;
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsConsistentBackup;
use Celikom\Website\CmsFullDbBackup;
use Celikom\Website\CmsRecoveryPair;
use Celikom\Website\Database;

function snapshotAssert(bool $test, string $why): void {
    if (!$test) throw new RuntimeException('Coordinated snapshot: '.$why);
}
function snapshotReject(callable $call, string $why): void {
    try { $call(); } catch (\Throwable $e) { return; }
    throw new RuntimeException('Unsafe coordinated snapshot accepted: '.$why);
}
$cfg = CmsConfig::databaseSettings();
if (getenv('CI') !== 'true' ||
    getenv('CELIKOM_SITE_SANDBOX_RESTORE') !== '1' ||
    $cfg['dbname'] !== 'celikom_site_test' || $cfg['host'] !== '127.0.0.1') {
    throw new RuntimeException('Coordinated snapshot test requires disposable CI MySQL');
}
$pdo = Database::connect($cfg);
$writer = Database::connect($cfg);
$base = dirname(__DIR__);
$temp = sys_get_temp_dir().'/celikom-consistent-'.bin2hex(random_bytes(10));
$bundle = $temp.'/bundle';
$media = $temp.'/media';
foreach ([$temp, $bundle, $media] as $path) {
    if (!mkdir($path, 0700)) throw new RuntimeException('Private CI fixture allocation failed');
}
$assetId = null;
$oldVersion = null;
$assetName = bin2hex(random_bytes(20)).'.png';
$assetPath = $media.'/'.$assetName;
$png = base64_decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=', true
);
snapshotAssert(is_string($png), 'synthetic PNG is missing');
$key = random_bytes(32);
try {
    file_put_contents($assetPath, $png);
    chmod($assetPath, 0600);
    $pdo->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,'.
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)')
        ->execute(['site-private/'.$assetName, 'consistent-test.png', 'image/png',
            hash('sha256', $png), 1, 1, 'CI synthetic', 1]);
    $assetId = (int)$pdo->lastInsertId();
    $oldVersion = $writer->query('SELECT optimistic_version FROM content_drafts WHERE id=1')
        ->fetchColumn();
    snapshotAssert($oldVersion !== false, 'Stage 9 editorial test state missing');
    $oldVersion = (int)$oldVersion;

    snapshotReject(fn() => CmsFullDbBackup::export(
        $pdo, $bundle, $base.'/public', $key, true
    ), 'unowned full DB snapshot');
    snapshotReject(fn() => CmsBackup::export(
        $pdo, $bundle, $media, $base.'/public', true
    ), 'unowned content snapshot');

    $pdo->exec('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
    $pdo->beginTransaction();
    $pdo->query('SELECT id FROM site_state WHERE id=1')->fetchAll(PDO::FETCH_ASSOC);
    $full = CmsFullDbBackup::export($pdo, $bundle, $base.'/public', $key, true);

    // Simulate a live editor committing on another connection while exports run.
    $writer->prepare('UPDATE content_drafts SET optimistic_version=? WHERE id=1')
        ->execute([$oldVersion + 1]);
    $content = CmsBackup::export($pdo, $bundle, $media, $base.'/public', true);
    snapshotAssert($pdo->inTransaction(), 'exporters committed the shared snapshot');
    $pdo->commit();
    $verified = CmsRecoveryPair::inspect($full, $content, $key, $base.'/public');
    snapshotAssert($verified['consistent'] &&
        $verified['media_files'] === 1, 'two exports diverged under concurrent edit');
    $payload = json_decode((string)file_get_contents($content), true,
        512, JSON_THROW_ON_ERROR)['payload'];
    snapshotAssert((int)$payload['tables']['content_drafts'][0]['optimistic_version'] ===
        $oldVersion, 'content export saw later editor transaction');
    snapshotAssert((int)$writer->query(
        'SELECT optimistic_version FROM content_drafts WHERE id=1'
    )->fetchColumn() === $oldVersion + 1, 'concurrent edit was not committed');
    $writer->prepare('UPDATE content_drafts SET optimistic_version=? WHERE id=1')
        ->execute([$oldVersion]);
    unlink($full);
    unlink($content);

    $capture = CmsConsistentBackup::capture(
        $pdo, $bundle, $media, $base.'/public', $key
    );
    $manifest = $capture['manifest'];
    snapshotAssert(is_file($manifest) &&
        (fileperms($manifest) & 0777) === 0600 &&
        $capture['report']['consistent'] &&
        $capture['report']['media_files'] === 1 &&
        $capture['report']['rows']['audit_log'] >= 1,
        'complete restore point lacks DB, history or binary private media');
    snapshotAssert(CmsConsistentBackup::inspect(
        $manifest, $key, $base.'/public'
    )['consistent'], 'restore manifest could not be reverified');
    snapshotReject(fn() => CmsConsistentBackup::inspect(
        $manifest, random_bytes(32), $base.'/public'
    ), 'wrong encrypted DB key');
    snapshotReject(fn() => CmsConsistentBackup::capture(
        $pdo, $base.'/public', $media, $base.'/public', $key
    ), 'backup written under public_html');
    $before = glob($bundle.'/*');
    unlink($assetPath);
    snapshotReject(fn() => CmsConsistentBackup::capture(
        $pdo, $bundle, $media, $base.'/public', $key
    ), 'missing immutable image during snapshot');
    snapshotAssert(glob($bundle.'/*') === $before,
        'failed export left an incomplete restore point');
    file_put_contents($assetPath, $png);
    chmod($assetPath, 0600);

    $manifestRaw = file_get_contents($manifest);
    $modified = json_decode($manifestRaw, true, 32, JSON_THROW_ON_ERROR);
    $modified['content_media']['sha256'] = str_repeat('0', 64);
    file_put_contents($manifest, json_encode($modified, JSON_THROW_ON_ERROR));
    snapshotReject(fn() => CmsConsistentBackup::inspect(
        $manifest, $key, $base.'/public'
    ), 'modified restore artifact digest');
    file_put_contents($manifest, $manifestRaw);
    chmod($manifest, 0644);
    snapshotReject(fn() => CmsConsistentBackup::inspect(
        $manifest, $key, $base.'/public'
    ), 'world-readable restore point manifest');
    chmod($manifest, 0600);

    echo "Stage10: single InnoDB snapshot despite concurrent CMS edit, authenticated complete restore point, broken media/permissions/digests rejected — PASS\n";
} finally {
    if ($pdo->inTransaction()) $pdo->rollBack();
    if ($oldVersion !== null) {
        $writer->prepare('UPDATE content_drafts SET optimistic_version=? WHERE id=1')
            ->execute([$oldVersion]);
    }
    if ($assetId !== null) {
        $pdo->prepare('DELETE FROM media_assets WHERE id=?')->execute([$assetId]);
    }
    foreach ([$bundle, $media] as $directory) {
        foreach (glob($directory.'/*') ?: [] as $item) {
            if (is_file($item) || is_link($item)) unlink($item);
        }
        rmdir($directory);
    }
    rmdir($temp);
}
