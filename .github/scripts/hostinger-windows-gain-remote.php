<?php
/**
 * W98 private Hostinger operator helper.
 * Reads approved active nonzero-gain rows, streams verified originals only to
 * the ephemeral runner, and checks real session-bound signed HTTPS Range URLs.
 * Never prints media bytes, storage paths, session identifiers, tokens or URLs.
 */
declare(strict_types=1);

use Celikom\Admin\AudioGainService;
use Celikom\Application\AudioTokenService;
use Celikom\Application\ResolveService;
use Celikom\Application\WindowsGainVariant;
use Celikom\Database\Connection;
use Celikom\Entitlement\EntitlementService;
use Celikom\Storage\LocalStorageAdapter;
use Celikom\Repositories\PdoCatalogRepository;

ini_set('display_errors', '0');

try {
    if (PHP_SAPI !== 'cli') throw new RuntimeException('cli_required');
    $operation = $argv[1] ?? '';
    $expectedSha = $argv[2] ?? '';
    if (!preg_match('/^[a-f0-9]{40}$/D', $expectedSha)) throw new RuntimeException('bad_run_identity');

    $siteRoot = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $expectedIncoming = $siteRoot . '/incoming/windows-gain-' . $expectedSha;
    $realIncoming = realpath(__DIR__);
    $realExpectedIncoming = realpath($expectedIncoming);
    if ($realIncoming === false || $realExpectedIncoming === false ||
        !hash_equals($realExpectedIncoming, $realIncoming) || is_link(__FILE__))
        throw new RuntimeException('private_helper_path_rejected');

    $release = realpath($siteRoot . '/current');
    if ($release === false || !str_starts_with($release, $siteRoot . '/releases/') ||
        !is_file($release . '/bootstrap.php'))
        throw new RuntimeException('active_release_path_rejected');

    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if (($config['environment'] ?? '') !== 'production' ||
        ($config['storage_driver'] ?? '') !== 'local')
        throw new RuntimeException('production_storage_contract_rejected');

    $pdo = Connection::open($config);
    $storage = new LocalStorageAdapter($config['storage_path']);
    $storageRoot = realpath($config['storage_path']);
    $expectedStorageRoot = realpath($siteRoot . '/shared/audio');
    if ($storageRoot === false || $expectedStorageRoot === false ||
        !hash_equals($expectedStorageRoot, $storageRoot))
        throw new RuntimeException('private_storage_root_rejected');

    $activeRows = static function () use ($pdo): array {
        $sql = "SELECT r.id AS replacement_id, t.service_track_id AS track_id,
                    r.version, r.gain_db, a.sha256 AS source_sha256,
                    a.duration_ms, a.size_bytes AS source_size_bytes,
                    a.mime_type, a.storage_driver, a.storage_key,
                    w.replacement_id AS sidecar_id, w.source_sha256 AS sidecar_source_sha256,
                    w.source_version AS sidecar_source_version, w.gain_db AS sidecar_gain_db,
                    w.storage_key AS sidecar_storage_key, w.sha256 AS sidecar_sha256,
                    w.size_bytes AS sidecar_size_bytes, w.duration_ms AS sidecar_duration_ms
                FROM track_replacements r
                JOIN tracks t ON t.id = r.track_id
                JOIN audio_assets a ON a.id = r.audio_asset_id
                LEFT JOIN windows_gain_variants w ON w.replacement_id = r.id
                WHERE r.status = 'approved' AND r.is_active = 1
                  AND r.disabled_at IS NULL AND r.gain_db <> 0
                ORDER BY r.id";
        return $pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC);
    };

    $hashStorage = static function (LocalStorageAdapter $storage, string $key): array {
        $stream = $storage->openStream($key);
        try {
            $hash = hash_init('sha256');
            $size = hash_update_stream($hash, $stream);
            if ($size === false) throw new RuntimeException('source_hash_read_failed');
            return ['sha256' => hash_final($hash), 'size_bytes' => (int)$size];
        } finally {
            fclose($stream);
        }
    };

    if ($operation === 'prepare') {
        $stage = $storageRoot . '/incoming/windows-gain';
        if (is_link($stage)) throw new RuntimeException('private_stage_symlink_rejected');
        if (!is_dir($stage) && !mkdir($stage, 0700, true) && !is_dir($stage))
            throw new RuntimeException('private_stage_create_failed');
        chmod($stage, 0700);
        echo "W98_PRIVATE_STAGE_READY\n";
        exit(0);
    }

    if ($operation === 'inventory') {
        $migrationFile = $release . '/migrations/020_windows_gain_variants.sql';
        $migrationQuery = $pdo->prepare('SELECT sha256 FROM schema_migrations WHERE version = ?');
        $migrationQuery->execute(['020_windows_gain_variants.sql']);
        $recorded = $migrationQuery->fetchColumn();
        $disk = is_file($migrationFile) ? hash_file('sha256', $migrationFile) : false;
        if (!is_string($recorded) || !is_string($disk) || !hash_equals($recorded, $disk))
            throw new RuntimeException('migration_020_not_applied_or_checksum_mismatch');

        $rows = $activeRows();
        if (count($rows) > 50) throw new RuntimeException('active_gain_inventory_exceeds_safe_batch');
        $catalog = new PdoCatalogRepository($pdo);
        $out = [];
        foreach ($rows as $row) {
            $id = (int)$row['replacement_id'];
            $trackId = (string)$row['track_id'];
            $version = (int)$row['version'];
            $gain = AudioGainService::value((string)$row['gain_db']);
            $sourceSha = (string)$row['source_sha256'];
            $sourceSize = (int)$row['source_size_bytes'];
            $duration = (int)$row['duration_ms'];
            if ($id < 1 || !preg_match('/^[1-9][0-9]{0,23}$/D', $trackId) ||
                $version < 1 || $gain == 0.0 || $gain < -12.0 || $gain > 12.0 ||
                !preg_match('/^[a-f0-9]{64}$/D', $sourceSha) ||
                $sourceSize < 1024 || $sourceSize > 31457280 ||
                $duration < 1000 || $row['mime_type'] !== 'audio/mpeg' ||
                $row['storage_driver'] !== 'local')
                throw new RuntimeException('active_gain_source_contract_rejected');

            $sourceCheck = $hashStorage($storage, (string)$row['storage_key']);
            if ($sourceCheck['size_bytes'] !== $sourceSize ||
                !hash_equals($sourceSha, $sourceCheck['sha256']))
                throw new RuntimeException('original_source_digest_mismatch');

            $alreadyStaged = false;
            $renderSha = '';
            $renderSize = 0;
            if ($row['sidecar_id'] !== null) {
                if (!hash_equals($sourceSha, (string)$row['sidecar_source_sha256']) ||
                    (int)$row['sidecar_source_version'] !== $version ||
                    abs((float)$row['sidecar_gain_db'] - $gain) > 0.00001 ||
                    !preg_match('/^[a-f0-9]{64}$/D', (string)$row['sidecar_sha256']) ||
                    (int)$row['sidecar_size_bytes'] < 1024)
                    throw new RuntimeException('existing_sidecar_identity_mismatch');
                $active = $catalog->findActive('yandex', $trackId);
                $selected = $active ? WindowsGainVariant::select($active, $storage) : null;
                if ($selected === null ||
                    !hash_equals((string)$row['sidecar_sha256'], (string)$selected['sha256']))
                    throw new RuntimeException('existing_sidecar_integrity_mismatch');
                $stored = $hashStorage($storage, (string)$row['sidecar_storage_key']);
                if ($stored['size_bytes'] !== (int)$row['sidecar_size_bytes'] ||
                    !hash_equals((string)$row['sidecar_sha256'], $stored['sha256']))
                    throw new RuntimeException('existing_sidecar_digest_mismatch');
                $alreadyStaged = true;
                $renderSha = (string)$row['sidecar_sha256'];
                $renderSize = (int)$row['sidecar_size_bytes'];
            }
            $out[] = [
                'replacement_id' => $id,
                'track_id' => $trackId,
                'version' => $version,
                'gain_db' => $gain,
                'source_sha256' => $sourceSha,
                'duration_ms' => $duration,
                'source_size_bytes' => $sourceSize,
                'already_staged' => $alreadyStaged,
                'render_sha256' => $renderSha,
                'render_size_bytes' => $renderSize,
            ];
        }
        echo json_encode(['schema_020' => true, 'count' => count($out), 'rows' => $out],
            JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES);
        echo "\n";
        exit(0);
    }

    if ($operation === 'source') {
        $idText = $argv[3] ?? '';
        $sourceSha = $argv[4] ?? '';
        if (!preg_match('/^[1-9][0-9]{0,17}$/D', $idText) ||
            !preg_match('/^[a-f0-9]{64}$/D', $sourceSha))
            throw new RuntimeException('bad_source_request');
        $query = $pdo->prepare("SELECT r.status,r.is_active,r.disabled_at,r.version,r.gain_db,
                    a.sha256,a.mime_type,a.storage_driver,a.storage_key,a.size_bytes
                FROM track_replacements r
                JOIN audio_assets a ON a.id = r.audio_asset_id
                WHERE r.id = ?");
        $query->execute([(int)$idText]);
        $row = $query->fetch(PDO::FETCH_ASSOC);
        if (!$row || $row['status'] !== 'approved' || (int)$row['is_active'] !== 1 ||
            $row['disabled_at'] !== null || $row['mime_type'] !== 'audio/mpeg' ||
            $row['storage_driver'] !== 'local' || !hash_equals($sourceSha, (string)$row['sha256']))
            throw new RuntimeException('source_changed_since_inventory');
        $stream = $storage->openStream((string)$row['storage_key']);
        $hash = hash_init('sha256');
        $bytes = 0;
        try {
            while (!feof($stream)) {
                $chunk = fread($stream, 65536);
                if ($chunk === false) throw new RuntimeException('source_stream_read_failed');
                if ($chunk === '') break;
                hash_update($hash, $chunk);
                $bytes += strlen($chunk);
                echo $chunk;
            }
        } finally {
            fclose($stream);
        }
        if ($bytes !== (int)$row['size_bytes'] || !hash_equals($sourceSha, hash_final($hash))) {
            fwrite(STDERR, "W98_SOURCE_DIGEST_MISMATCH\n");
            exit(2);
        }
        exit(0);
    }

    if ($operation === 'live-verify') {
        if (($config['auth_enabled'] ?? false) !== true ||
            ($config['entitlement_enabled'] ?? false) !== true ||
            ($config['api_enabled'] ?? false) !== true ||
            strlen((string)($config['audio_signing_key'] ?? '')) < 32)
            throw new RuntimeException('live_auth_entitlement_or_signing_not_enabled');

        $rows = $activeRows();
        if (!$rows) throw new RuntimeException('no_active_nonzero_gain_rows');

        // The owner explicitly authorized this one account by email. Read the
        // address from SSH stdin (never argv/logs), then select only its session.
        $ownerEmail = strtolower(trim((string)stream_get_contents(STDIN)));
        if ($ownerEmail === '' || strlen($ownerEmail) > 254 ||
            filter_var($ownerEmail, FILTER_VALIDATE_EMAIL) === false) {
            throw new RuntimeException('explicit_owner_email_required');
        }
        $sessionQuery = $pdo->prepare("SELECT s.id,s.user_id,s.refresh_expires_at
            FROM user_sessions s
            INNER JOIN users u ON u.id = s.user_id
            WHERE u.email = ?
              AND u.status = 'active'
              AND s.revoked_at IS NULL
              AND s.refresh_expires_at > UTC_TIMESTAMP(6)
            ORDER BY s.id DESC LIMIT 1");
        $sessionQuery->execute([$ownerEmail]);
        $session = $sessionQuery->fetch(PDO::FETCH_ASSOC);
        if (!$session) throw new RuntimeException('authorized_owner_session_not_available');

        $entitlements = new EntitlementService($pdo, (bool)($config['paid_entitlement_enabled'] ?? false));
        $decision = $entitlements->check((int)$session['user_id']);
        if (!$decision->allowed) {
            throw new RuntimeException('authorized_owner_entitlement_not_active');
        }
        $access = [
            'session_id' => (int)$session['id'],
            'refresh_expires_at' => (string)$session['refresh_expires_at'],
            'valid_until' => $decision->validUntil,
        ];

        $catalog = new PdoCatalogRepository($pdo);
        $tokens = new AudioTokenService((string)$config['audio_signing_key'], (int)$config['audio_token_ttl']);
        $resolver = new ResolveService($catalog, $storage, $tokens,
            (int)$config['resolve_cache_ttl_seconds'], (int)$config['negative_cache_ttl_seconds']);
        $origin = 'https://darkred-camel-588676.hostingersite.com';
        $checks = [];
        foreach ($rows as $row) {
            $trackId = (string)$row['track_id'];
            $replacementId = (int)$row['replacement_id'];
            $version = (int)$row['version'];
            $gain = AudioGainService::value((string)$row['gain_db']);
            $active = $catalog->findActive('yandex', $trackId);
            $variant = $active ? WindowsGainVariant::select($active, $storage) : null;
            if ($variant === null) throw new RuntimeException('live_sidecar_not_selectable');
            $resolved = $resolver->resolve('yandex', $trackId, $access, true, true);
            if (($resolved['found'] ?? false) !== true ||
                ($resolved['gain_applied'] ?? false) !== true ||
                (int)($resolved['replacement_id'] ?? 0) !== $replacementId ||
                abs((float)($resolved['gain_db'] ?? 0) - $gain) > 0.00001 ||
                !str_contains((string)($resolved['audio_url'] ?? ''), 'variant=windows_gain_v1') ||
                !str_contains((string)($resolved['audio_url'] ?? ''), '&sid='.(int)$session['id']))
                throw new RuntimeException('live_resolve_did_not_select_windows_gain');

            $size = (int)$variant['size_bytes'];
            $end = min(65535, $size - 1);
            $expectedLength = $end + 1;
            $url = $origin . (string)$resolved['audio_url'];
            $context = stream_context_create([
                'http' => [
                    'method' => 'GET',
                    'header' => "Range: bytes=0-$end\r\nAccept-Encoding: identity\r\nConnection: close\r\n",
                    'timeout' => 20,
                    'ignore_errors' => true,
                    'follow_location' => 0,
                    'protocol_version' => 1.1,
                    'user_agent' => 'CELIKOM-W98-Live-Range-Check',
                ],
                'ssl' => ['verify_peer' => true, 'verify_peer_name' => true],
            ]);
            $body = @file_get_contents($url, false, $context);
            $headers = $http_response_header ?? [];
            if (!is_string($body)) throw new RuntimeException('live_signed_range_transport_failed');
            $statusLine = (string)($headers[0] ?? '');
            if (!preg_match('/\s206(?:\s|$)/', $statusLine))
                throw new RuntimeException('live_signed_range_status_not_206');
            $headerMap = [];
            foreach ($headers as $header) {
                $separator = strpos($header, ':');
                if ($separator === false) continue;
                $headerMap[strtolower(trim(substr($header, 0, $separator)))] = trim(substr($header, $separator + 1));
            }
            $expectedRange = "bytes 0-$end/$size";
            $expectedEtag = '"' . (string)$variant['sha256'] . '-' . $version . '"';
            if (strlen($body) !== $expectedLength ||
                ($headerMap['content-range'] ?? '') !== $expectedRange ||
                (int)($headerMap['content-length'] ?? 0) !== $expectedLength ||
                !str_starts_with(strtolower((string)($headerMap['content-type'] ?? '')), 'audio/mpeg') ||
                !hash_equals($expectedEtag, (string)($headerMap['etag'] ?? '')))
                throw new RuntimeException('live_signed_range_headers_or_bytes_mismatch');

            $checks[] = [
                'replacement_id' => $replacementId,
                'track_id' => $trackId,
                'version' => $version,
                'gain_db' => $gain,
                'source_sha256' => (string)$row['source_sha256'],
                'sidecar_sha256' => (string)$variant['sha256'],
                'duration_ms' => (int)$row['duration_ms'],
                'source_size_bytes' => (int)$row['source_size_bytes'],
                'gain_applied' => true,
                'http_status' => 206,
                'range_bytes' => $expectedLength,
                'content_type' => 'audio/mpeg',
                'etag_verified' => true,
            ];
            unset($body, $headers, $url, $resolved);
        }
        echo json_encode(['count' => count($checks), 'session_entitled' => true, 'checks' => $checks],
            JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES);
        echo "\n";
        exit(0);
    }

    throw new RuntimeException('unsupported_operation');
} catch (Throwable $error) {
    fwrite(STDERR, 'W98_PRIVATE_GAIN_REMOTE_REJECTED_' . get_class($error) . "\n");
    exit(2);
}
