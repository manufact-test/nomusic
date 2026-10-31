<?php
declare(strict_types=1);
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli' || count($argv) !== 2) exit(2);
try {
    $site = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
    $appDir = $site . '/celikom';
    $release = realpath($appDir . '/current');
    $path = realpath($argv[1]);
    if (!$release || !str_starts_with($release, $appDir . '/releases/') ||
        !$path || !str_starts_with($path, $appDir . '/incoming/stage7-smoke-') ||
        !is_file($path) || filesize($path) < 2097152 || filesize($path) > 5000000)
        throw new RuntimeException('fixture_layout');
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if (!$config['owner_uploads_enabled'] || strlen($config['owner_upload_token']) < 40
        || $config['environment'] !== 'production') throw new RuntimeException('owner_gate_not_ready');
    $pdo = Celikom\Database\Connection::open($config);
    $active = $pdo->query("SELECT a.sha256, a.storage_key, r.status, r.is_active
      FROM track_replacements r JOIN audio_assets a ON r.audio_asset_id=a.id WHERE r.id=1")->fetch(PDO::FETCH_ASSOC);
    if (!$active || $active['status'] !== 'approved' || (int)$active['is_active'] !== 1 ||
        !hash_equals($active['sha256'], hash_file('sha256', $appDir.'/shared/audio/'.$active['storage_key'])))
        throw new RuntimeException('active_audio_corrupt');
    $uuid = '00000000-0000-4000-8000-000000000075';
    $fields = [
      'service' => 'yandex', 'track_id' => '799133075', 'duration_ms' => '165000',
      'title' => 'synthetic-stage7-ci', 'artist' => 'celikom-ci', 'album' => '',
      'declaration' => '1', 'request_id' => $uuid
    ];
    if (!function_exists('curl_init')) throw new RuntimeException('php_curl_missing');
    $ch = curl_init('https://darkred-camel-588676.hostingersite.com/api/v1/uploads');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POSTFIELDS => $fields + ['file' => new CURLFile($path, 'audio/mpeg', 'ci-synth.mp3')],
        CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . $config['owner_upload_token']],
        CURLOPT_TIMEOUT => 90,
        CURLOPT_CONNECTTIMEOUT => 15,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_SSL_VERIFYPEER => true,
    ]);
    $body = curl_exec($ch);
    $http = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);
    if ($http !== 202 || !is_string($body)) {
        echo "PRIVATE_SMOKE_STATUS=", $http, "\n";
        throw new RuntimeException('https_upload_failed');
    }
    $payload = json_decode($body, true, 16, JSON_THROW_ON_ERROR);
    if (($payload['status'] ?? null) !== 'pending' || !is_int($payload['replacement_id']))
        throw new RuntimeException('wrong_upload_status');
    $stm = $pdo->prepare("SELECT r.status, r.is_active, a.sha256 FROM track_replacements r
      JOIN audio_assets a ON a.id=r.audio_asset_id
      JOIN tracks t ON t.id=r.track_id WHERE t.service='yandex' AND t.service_track_id='799133075'");
    $stm->execute();
    $pending = $stm->fetch(PDO::FETCH_ASSOC);
    if (!$pending || $pending['status'] !== 'pending' || (int)$pending['is_active'] !== 0 ||
        $pending['sha256'] !== hash_file('sha256', $path)) throw new RuntimeException('pending_integrity_failed');
    $after = $pdo->query("SELECT a.sha256,r.status,r.is_active FROM track_replacements r
      JOIN audio_assets a ON r.audio_asset_id=a.id WHERE r.id=1")->fetch(PDO::FETCH_ASSOC);
    if ($after['sha256'] !== $active['sha256'] || $after['status'] !== 'approved' ||
        (int)$after['is_active'] !== 1) throw new RuntimeException('approved_changed');
    echo "Stage7 HTTPS private MP3 upload: pending-only, existing approved unchanged. PASS\n";
} catch (Throwable) {
    fwrite(STDERR, "Stage7 HTTPS test failed; inspect safe status above, no credentials printed.\n");
    exit(1);
}
