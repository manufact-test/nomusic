<?php
declare(strict_types=1);
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli' || count($argv) !== 1) exit(2);
try {
    $app = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release = realpath($app . '/current');
    if (!$release || !is_link($app . '/current') ||
        !str_starts_with($release, $app . '/releases/') ||
        !is_file($release . '/src/Application/UploadService.php')) throw new RuntimeException('wrong_release');
    $shared = $app . '/shared';
    $file = $shared . '/env';
    if (is_link($shared) || is_link($file) || !is_file($file) ||
        (fileperms($file) & 0077)) throw new RuntimeException('unsafe_environment');
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['db_name'] !== 'u235811320_celikom') throw new RuntimeException('wrong_db');
    $pdo = Celikom\Database\Connection::open($config);
    $row = $pdo->query("SELECT r.id, r.status, r.is_active, a.sha256, a.storage_key
        FROM track_replacements r JOIN audio_assets a ON a.id = r.audio_asset_id WHERE r.id=1")->fetch(PDO::FETCH_ASSOC);
    if (!$row || $row['status'] !== 'approved' || (int)$row['is_active'] !== 1
        || !preg_match('/^[a-f0-9]{64}$/D', $row['sha256'])) throw new RuntimeException('active_track_changed');
    $audio = $shared . '/audio/' . $row['storage_key'];
    if (!is_file($audio) || !hash_equals($row['sha256'], hash_file('sha256', $audio))) throw new RuntimeException('active_audio_changed');
    foreach (['upload_submissions', 'audio_fingerprint_jobs', 'upload_rate_buckets'] as $table) {
        $stmt = $pdo->prepare("SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = ?");
        $stmt->execute([$table]);
        if ((int)$stmt->fetchColumn() !== 1) throw new RuntimeException('missing_stage7_migration');
    }
    $token = trim((string)stream_get_contents(STDIN, 256));
    if (!preg_match('/^[a-f0-9]{96}$/D', $token)) throw new RuntimeException('bad_owner_token');
    $lines = (string)file_get_contents($file);
    if ($lines === '' || strlen($lines) > 8192) throw new RuntimeException('environment_unreadable');
    $lines = preg_replace('/^(?:UPLOAD_OWNER_TOKEN|FEATURE_OWNER_UPLOADS)\s*=.*(?:\n|$)/m', '', $lines);
    if (!is_string($lines)) throw new RuntimeException('environment_invalid');
    $lines = rtrim($lines, "\r\n") . "\nFEATURE_OWNER_UPLOADS=1\nUPLOAD_OWNER_TOKEN=" . $token . "\n";
    $temp = tempnam($shared, '.stage7-env-');
    if ($temp === false) throw new RuntimeException('temp_failed');
    try {
        if (!chmod($temp, 0600) || file_put_contents($temp, $lines, LOCK_EX) !== strlen($lines)
            || !rename($temp, $file)) throw new RuntimeException('write_failed');
    } finally {
        if (file_exists($temp)) unlink($temp);
    }
    echo "Stage 7 owner upload enabled on dedicated CELIKOM private-test website; approved audio verified unchanged.\n";
} catch (Throwable) {
    fwrite(STDERR, "Stage 7 owner gate provisioning failed; no private values disclosed.\n");
    exit(1);
}
