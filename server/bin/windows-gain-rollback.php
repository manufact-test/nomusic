<?php
/**
 * W98 operations-only rollback for one exact Windows gain sidecar.
 * Never changes track_replacements, audio_assets, or original source media.
 */
declare(strict_types=1);

if (PHP_SAPI !== 'cli') exit(2);
if (in_array('--help', $argv, true)) {
    echo "W98 private Windows gain rollback. Requires explicit rollback authorization.\n";
    echo "--replacement=ID --source-sha=HEX64 --source-version=INT --gain-db=DB --render-sha=HEX64\n";
    exit(0);
}
require dirname(__DIR__).'/bootstrap.php';

use Celikom\Admin\AudioGainService;
use Celikom\Database\Connection;
use Celikom\Storage\LocalStorageAdapter;

try {
    $options = [];
    foreach (array_slice($argv, 1) as $entry) {
        if (!preg_match('/^--(replacement|source-sha|source-version|gain-db|render-sha)=(.+)$/D', $entry, $match)
            || isset($options[$match[1]])) throw new InvalidArgumentException('bad_args');
        $options[$match[1]] = $match[2];
    }
    $idText = $options['replacement'] ?? '';
    $versionText = $options['source-version'] ?? '';
    $sourceSha = $options['source-sha'] ?? '';
    $renderSha = $options['render-sha'] ?? '';
    if (!preg_match('/^[1-9][0-9]{0,17}$/D', $idText)
        || !preg_match('/^[1-9][0-9]{0,8}$/D', $versionText)
        || !preg_match('/^[a-f0-9]{64}$/D', $sourceSha)
        || !preg_match('/^[a-f0-9]{64}$/D', $renderSha)
        || !is_string($options['gain-db'] ?? null))
        throw new InvalidArgumentException('bad_args');
    if (getenv('CELIKOM_W93_ENABLE_ROLLBACK') !== 'YES_EXPLICIT_PRIVATE_ROLLBACK')
        throw new DomainException('explicit_rollback_authorization_required');

    $replacementId = (int)$idText;
    $sourceVersion = (int)$versionText;
    $gainDb = AudioGainService::value($options['gain-db']);
    if ($gainDb == 0.0) throw new InvalidArgumentException('zero_gain_has_no_sidecar');
    $expectedKey = 'windows-gain/'.substr($renderSha,0,2).'/'.$renderSha.'.mp3';

    $config = require dirname(__DIR__).'/config/app.php';
    if (($config['storage_driver'] ?? null) !== 'local')
        throw new RuntimeException('storage_driver_not_supported');
    $storage = new LocalStorageAdapter($config['storage_path']);
    $pdo = Connection::open($config);
    $pdo->beginTransaction();
    try {
        $query = $pdo->prepare('SELECT source_sha256,source_version,gain_db,storage_key,sha256
            FROM windows_gain_variants WHERE replacement_id = ? FOR UPDATE');
        $query->execute([$replacementId]);
        $row = $query->fetch(PDO::FETCH_ASSOC);
        if (!$row) {
            $pdo->rollBack();
            echo "W98_PRIVATE_WINDOWS_GAIN_ROLLBACK_NOOP\n";
            exit(0);
        }
        if (!hash_equals($sourceSha, (string)$row['source_sha256'])
            || (int)$row['source_version'] !== $sourceVersion
            || abs((float)$row['gain_db'] - $gainDb) > 0.00001
            || !hash_equals($renderSha, (string)$row['sha256'])
            || !hash_equals($expectedKey, (string)$row['storage_key']))
            throw new DomainException('rollback_identity_mismatch');

        $refs = $pdo->prepare('SELECT COUNT(*) FROM windows_gain_variants
            WHERE storage_key = ? AND replacement_id <> ?');
        $refs->execute([$expectedKey, $replacementId]);
        $shared = (int)$refs->fetchColumn() > 0;
        $delete = $pdo->prepare('DELETE FROM windows_gain_variants WHERE replacement_id = ?');
        $delete->execute([$replacementId]);
        if ($delete->rowCount() !== 1) throw new RuntimeException('rollback_row_delete_failed');
        $pdo->commit();

        if (!$shared && $storage->exists($expectedKey)) $storage->delete($expectedKey);
        echo "W98_PRIVATE_WINDOWS_GAIN_ROLLBACK_PASS\n";
    } catch (Throwable $error) {
        if ($pdo->inTransaction()) $pdo->rollBack();
        throw $error;
    }
} catch (Throwable $error) {
    fwrite(STDERR, 'W98_GAIN_ROLLBACK_REJECTED_'.get_class($error)."\n");
    exit(2);
}
