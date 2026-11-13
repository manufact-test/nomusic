<?php
/**
 * W93 OPERATIONS-ONLY CLI, NEVER called by web/cron/deploy.
 * Strict source/digest/version/gain gates, private staging, dry-run default.
 * Real media never appears in logs or API payloads.
 */
declare(strict_types=1);

if (PHP_SAPI !== 'cli') exit(2);
if (in_array('--help', $argv, true)) {
    echo "W93 private Windows gain stager. No network fetch/transcode. Default dry-run.\n";
    echo "--replacement=ID --source-sha=HEX64 --source-version=INT --gain-db=DB --render-sha=HEX64 --file=PRIVATE_STAGE_MP3 [--commit]\n";
    exit(0);
}
require dirname(__DIR__).'/bootstrap.php';

use Celikom\Admin\AudioGainService;
use Celikom\Application\Mp3Inspector;
use Celikom\Database\Connection;
use Celikom\Storage\LocalStorageAdapter;

try {
    $options = [];
    foreach (array_slice($argv, 1) as $entry) {
        if ($entry === '--commit') { $options['commit'] = true; continue; }
        if (!preg_match('/^--(replacement|source-sha|source-version|gain-db|render-sha|file)=(.+)$/D', $entry, $match)
            || isset($options[$match[1]])) throw new InvalidArgumentException('bad_args');
        $options[$match[1]] = $match[2];
    }
    $idText = $options['replacement'] ?? '';
    $versionText = $options['source-version'] ?? '';
    $sourceSha = $options['source-sha'] ?? '';
    $renderSha = $options['render-sha'] ?? '';
    $input = $options['file'] ?? '';
    if (!is_string($idText) || !preg_match('/^[1-9][0-9]{0,17}$/D', $idText)
        || !is_string($versionText) || !preg_match('/^[1-9][0-9]{0,8}$/D', $versionText)
        || !is_string($sourceSha) || !preg_match('/^[a-f0-9]{64}$/D', $sourceSha)
        || !is_string($renderSha) || !preg_match('/^[a-f0-9]{64}$/D', $renderSha)
        || !is_string($input) || $input === '' || !is_string($options['gain-db'] ?? null))
        throw new InvalidArgumentException('bad_args');
    $replacementId = (int)$idText;
    $expectedVersion = (int)$versionText;
    $gainDb = AudioGainService::value($options['gain-db']);
    if ($gainDb == 0.0) throw new InvalidArgumentException('zero_gain_has_no_sidecar');
    $commit = ($options['commit'] ?? false) === true;
    if ($commit && getenv('CELIKOM_W93_ENABLE_STAGE') !== 'YES_EXPLICIT_PRIVATE_STAGE')
        throw new DomainException('explicit_stage_authorization_required');

    $config = require dirname(__DIR__).'/config/app.php';
    if (($config['storage_driver'] ?? null) !== 'local')
        throw new RuntimeException('storage_driver_not_supported');
    $storage = new LocalStorageAdapter($config['storage_path']);
    $stage = realpath(rtrim($config['storage_path'],'/').'/incoming/windows-gain');
    $source = realpath($input);
    if (!is_string($stage) || !is_dir($stage)
        || !is_string($source) || !str_starts_with($source, $stage.DIRECTORY_SEPARATOR)
        || is_link($input) || !is_file($source))
        throw new DomainException('file_not_private_staging');
    $size = filesize($source);
    if (!is_int($size) || $size < 1024 || $size > 31457280)
        throw new DomainException('invalid_render_size');
    if (!hash_equals($renderSha, hash_file('sha256', $source) ?: ''))
        throw new DomainException('render_hash_mismatch');
    $duration = (new Mp3Inspector())->durationMs($source);
    if (!is_int($duration) || $duration < 1000) throw new DomainException('invalid_mp3');
    $key = 'windows-gain/'.substr($renderSha,0,2).'/'.$renderSha.'.mp3';
    $pdo = Connection::open($config);
    $pdo->beginTransaction();
    $existing = null;
    $createdNewObject = false;
    try {
        $lock = $pdo->prepare("SELECT r.id,r.status,r.is_active,r.disabled_at,r.version,r.gain_db,
            a.sha256,a.mime_type,a.duration_ms,a.storage_driver
            FROM track_replacements r JOIN audio_assets a ON a.id = r.audio_asset_id
            WHERE r.id=? FOR UPDATE");
        $lock->execute([$replacementId]);
        $row = $lock->fetch(PDO::FETCH_ASSOC);
        if (!$row || $row['status']!=='approved' || (int)$row['is_active']!==1 ||
            $row['disabled_at'] !== null || (int)$row['version']!==$expectedVersion ||
            !hash_equals($sourceSha, (string)$row['sha256']) ||
            abs((float)$row['gain_db']-$gainDb)>0.00001 ||
            $row['mime_type']!=='audio/mpeg' || $row['storage_driver']!=='local' ||
            abs((int)$row['duration_ms']-$duration)>1500)
            throw new DomainException('approved_version_source_or_gain_changed');
        $get = $pdo->prepare('SELECT source_sha256,source_version,gain_db,sha256,size_bytes
            FROM windows_gain_variants WHERE replacement_id=? FOR UPDATE');
        $get->execute([$replacementId]);
        $existing = $get->fetch(PDO::FETCH_ASSOC);
        if ($existing && ($existing['source_sha256']!==$sourceSha ||
            (int)$existing['source_version']!==$expectedVersion ||
            abs((float)$existing['gain_db']-$gainDb)>0.00001 ||
            $existing['sha256']!==$renderSha || (int)$existing['size_bytes']!==$size))
            throw new DomainException('sidecar_exists_manual_retirement_required');
        if ($commit && !$storage->exists($key)) {
            $stream = fopen($source, 'rb');
            if (!is_resource($stream)) throw new RuntimeException('stage_read_failure');
            try { $storage->put($key,$stream); $createdNewObject = true; } finally { fclose($stream); }
        }
        if ($commit) {
            if (!$storage->exists($key) || $storage->getSize($key)!==$size)
                throw new RuntimeException('render_storage_mismatch');
            $file = $storage->openStream($key);
            try {
                $hash = hash_init('sha256');
                hash_update_stream($hash,$file);
                if (!hash_equals($renderSha, hash_final($hash)))
                    throw new RuntimeException('stored_render_hash_mismatch');
            } finally { fclose($file); }
            if (!$existing) {
                $insert = $pdo->prepare('INSERT INTO windows_gain_variants
                   (replacement_id,source_sha256,source_version,gain_db,storage_key,sha256,
                     mime_type,size_bytes,duration_ms)
                   VALUES (?,?,?, ?,?,?, ?,?,?)');
                $insert->execute([$replacementId,$sourceSha,$expectedVersion,$gainDb,
                    $key,$renderSha,'audio/mpeg',$size,$duration]);
            }
            $pdo->commit();
            echo 'W93_PRIVATE_WINDOWS_GAIN_STAGED'."\n";
        } else {
            $pdo->rollBack();
            echo 'W93_PRIVATE_WINDOWS_GAIN_DRY_RUN_PASS_NO_WRITE'."\n";
        }
    } catch (Throwable $error) {
        if ($pdo->inTransaction()) $pdo->rollBack();
        // A failed first insert must not leave an unreferenced private render.
        // Existing rows may have been repaired, so those objects are retained.
        if ($commit && !$existing && isset($storage, $key)) {
            try {
                $refs = $pdo->prepare('SELECT COUNT(*) FROM windows_gain_variants WHERE storage_key = ?');
                $refs->execute([$key]);
                if ((int)$refs->fetchColumn() === 0 && $storage->exists($key)) $storage->delete($key);
            } catch (Throwable) { /* An orphan remains private and is safe to clean later. */ }
        }
        throw $error;
    }
} catch (Throwable $error) {
    // No paths, SQL, credentials, music bytes or signed URLs in errors.
    fwrite(STDERR,'W93_GAIN_STAGE_REJECTED_'.get_class($error)."\n");
    exit(2);
}
