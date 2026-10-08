<?php
declare(strict_types=1);

/**
 * Restricted owner-only Stage 5 operations. Uploaded by a pinned GitHub Actions
 * SSH connection and executed from CELIKOM/incoming, NEVER the public web root.
 * Never echo tokens, environment contents, private filenames or SQL errors.
 */
if (PHP_SAPI !== 'cli' || count($argv) !== 2) {
    exit(2);
}
ini_set('display_errors', '0');

try {
    $site = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
    $app = $site . '/celikom';
    if (realpath(dirname(__DIR__, 2)) !== $app || is_link($app) || !is_dir($site . '/public_html')) {
        throw new RuntimeException('invalid_private_layout');
    }
    $shared = $app . '/shared';
    $staging = $shared . '/staging';
    $envPath = $shared . '/env';
    $release = realpath($app . '/current');
    if (!is_link($app . '/current') || $release === false || !str_starts_with($release, $app . '/releases/')
        || is_link($shared) || is_link($staging) || is_link($envPath)
        || realpath($staging) !== $staging || !is_file($envPath) || filesize($envPath) > 16384) {
        throw new RuntimeException('private_environment_not_ready');
    }
    $requestPath = $argv[1];
    if (realpath($requestPath) !== __DIR__ . '/hostinger-audio-request.json' || filesize($requestPath) > 2048) {
        throw new RuntimeException('invalid_operation_request');
    }
    $request = json_decode((string) file_get_contents($requestPath), true, 8, JSON_THROW_ON_ERROR);
    $fields = [
        'inspect' => ['operation'],
        'selftest' => ['operation', 'track_id'],
        'probe' => ['operation'],
        'import' => ['operation', 'track_id', 'duration_ms', 'confirm_reviewed'],
        'enable' => ['operation', 'track_id'],
        'disable' => ['operation'],
    ];
    $operation = is_array($request) ? ($request['operation'] ?? null) : null;
    if (!is_string($operation) || !isset($fields[$operation])) {
        throw new RuntimeException('invalid_operation_request');
    }
    $names = array_keys($request);
    sort($names);
    $allowed = $fields[$operation];
    sort($allowed);
    if ($names !== $allowed) {
        throw new RuntimeException('invalid_operation_request');
    }
    if (in_array($operation, ['import', 'enable', 'selftest'], true)
        && (!is_string($request['track_id']) || !preg_match('/^[1-9][0-9]{0,23}$/D', $request['track_id']))) {
        throw new RuntimeException('invalid_track_id');
    }

    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['environment'] !== 'production' || $config['storage_driver'] !== 'local'
        || realpath($config['storage_path']) !== $shared . '/audio') {
        throw new RuntimeException('invalid_runtime_environment');
    }
    $env = (string) file_get_contents($envPath);
    if (preg_match_all('/^FEATURE_REPLACEMENTS="[01]"\r?$/m', $env) !== 1
        || preg_match_all('/^FEATURE_ANALYTICS="0"\r?$/m', $env) !== 1) {
        throw new RuntimeException('unexpected_feature_configuration');
    }
    $isOn = (bool) preg_match('/^FEATURE_REPLACEMENTS="1"\r?$/m', $env);

    if ($operation === 'inspect') {
        echo 'Private staging and configuration validated; replacements: ', $isOn ? 'enabled' : 'disabled', "; analytics: disabled.\n";
        exit(0);
    }

    if ($operation === 'selftest') {
        // Exercise the current release's real application, DB mapping, authorization
        // and signed audio headers in-process. Do not print any credentials or URLs.
        if (!$isOn || strlen((string) $config['test_api_token']) < 24) {
            throw new RuntimeException('selftest_not_ready');
        }
        $service = new Celikom\Application($config);
        $res = $service->handle('GET', '/api/v1/resolve',
            ['service' => 'yandex', 'track_id' => $request['track_id']],
            ['authorization' => 'Bearer ' . $config['test_api_token']]);
        $answer = json_decode($res->body, true, 8, JSON_THROW_ON_ERROR);
        if ($res->status !== 200 || !is_array($answer)
            || ($answer['found'] ?? false) !== true || ($answer['replacement_id'] ?? null) !== 1
            || ($answer['duration_ms'] ?? null) !== 180872) {
            throw new RuntimeException('selftest_resolve_failed');
        }
        $url = parse_url((string) ($answer['audio_url'] ?? ''));
        if (!is_array($url) || !isset($url['path'], $url['query'])
            || $url['path'] !== '/api/v1/audio/1') {
            throw new RuntimeException('selftest_audio_url_failed');
        }
        parse_str($url['query'], $query);
        $audio = $service->handle('HEAD', $url['path'], $query, []);
        if ($audio->status !== 200 || ($audio->headers['Accept-Ranges'] ?? '') !== 'bytes'
            || (int) ($audio->headers['Content-Length'] ?? 0) < 1000000) {
            throw new RuntimeException('selftest_audio_headers_failed');
        }
        // Verify that the real HTTPS frontend forwards Authorization to PHP.
        // The token stays in the PHP request header, never in stdout or GitHub.
        $urlHttps = 'https://darkred-camel-588676.hostingersite.com/api/v1/resolve?service=yandex&track_id=' . rawurlencode($request['track_id']);
        $publicBody = false;
        $httpStatus = 0;
        if (function_exists('curl_init')) {
            $handle = curl_init($urlHttps);
            curl_setopt_array($handle, [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT => 15,
                CURLOPT_CONNECTTIMEOUT => 8,
                CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . $config['test_api_token']],
                CURLOPT_FOLLOWLOCATION => false,
                CURLOPT_MAXREDIRS => 0,
                CURLOPT_SSL_VERIFYPEER => true,
                CURLOPT_SSL_VERIFYHOST => 2,
            ]);
            $publicBody = curl_exec($handle);
            $httpStatus = (int) curl_getinfo($handle, CURLINFO_RESPONSE_CODE);
            curl_close($handle);
        } else {
            $context = stream_context_create([
                'http' => [
                    'method' => 'GET',
                    'header' => 'Authorization: Bearer ' . $config['test_api_token'] . "\r\n",
                    'timeout' => 15,
                    'ignore_errors' => true,
                    'follow_location' => 0,
                ],
            ]);
            $publicBody = @file_get_contents($urlHttps, false, $context);
            if (isset($http_response_header[0]) && preg_match('~^HTTP/[^ ]+ ([0-9]{3})~', $http_response_header[0], $matched)) {
                $httpStatus = (int) $matched[1];
            }
        }
        if ($httpStatus !== 200 || !is_string($publicBody)) {
            echo 'Public HTTPS authorized HTTP status: ' . $httpStatus . "\n";
            throw new RuntimeException('public_authorization_failed');
        }
        $publicResult = json_decode($publicBody, true, 8, JSON_THROW_ON_ERROR);
        if (!is_array($publicResult) || ($publicResult['found'] ?? false) !== true
            || ($publicResult['replacement_id'] ?? null) !== 1) {
            throw new RuntimeException('public_authorization_response_invalid');
        }
        // Exercise the actual public HTTPS audio stream with the same Origin and
        // byte range a browser media element requests; never expose signed URLs.
        $signedAudioUrl = 'https://darkred-camel-588676.hostingersite.com' . $answer['audio_url'];
        $mediaStatus = 0;
        $mediaHeaders = [];
        $mediaBytes = false;
        if (function_exists('curl_init')) {
            $handle = curl_init($signedAudioUrl);
            curl_setopt_array($handle, [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT => 20,
                CURLOPT_CONNECTTIMEOUT => 8,
                CURLOPT_HTTPHEADER => [
                    'Origin: https://music.yandex.ru',
                    'Range: bytes=0-1023',
                ],
                CURLOPT_FOLLOWLOCATION => false,
                CURLOPT_SSL_VERIFYPEER => true,
                CURLOPT_SSL_VERIFYHOST => 2,
                CURLOPT_HEADERFUNCTION => static function ($ch, string $headerLine) use (&$mediaHeaders): int {
                    $parts = explode(':', $headerLine, 2);
                    if (count($parts) === 2) {
                        $key = strtolower(trim($parts[0]));
                        if (in_array($key, ['content-type', 'content-length', 'content-range',
                            'accept-ranges', 'access-control-allow-origin'], true)) {
                            $mediaHeaders[$key] = trim($parts[1]);
                        }
                    }
                    return strlen($headerLine);
                },
            ]);
            $mediaBytes = curl_exec($handle);
            $mediaStatus = (int) curl_getinfo($handle, CURLINFO_RESPONSE_CODE);
            curl_close($handle);
        } else {
            $context = stream_context_create(['http' => [
                'method' => 'GET',
                'header' => "Origin: https://music.yandex.ru\r\nRange: bytes=0-1023\r\n",
                'timeout' => 20,
                'ignore_errors' => true,
                'follow_location' => 0,
            ]]);
            $mediaBytes = @file_get_contents($signedAudioUrl, false, $context);
            foreach (($http_response_header ?? []) as $line) {
                if (preg_match('~^HTTP/[^ ]+ ([0-9]{3})~', $line, $statusParts)) {
                    $mediaStatus = (int) $statusParts[1];
                }
                $parts = explode(':', $line, 2);
                if (count($parts) === 2) {
                    $key = strtolower(trim($parts[0]));
                    if (in_array($key, ['content-type', 'content-length', 'content-range',
                        'accept-ranges', 'access-control-allow-origin'], true)) {
                        $mediaHeaders[$key] = trim($parts[1]);
                    }
                }
            }
        }
        // Log status and non-secret headers ONLY; never log URLs or media bytes.
        echo 'Public signed audio: HTTP ', $mediaStatus,
            '; content type ', ($mediaHeaders['content-type'] ?? 'missing'),
            '; CORS ', ($mediaHeaders['access-control-allow-origin'] ?? 'missing'),
            '; accept ranges ', ($mediaHeaders['accept-ranges'] ?? 'missing'),
            '; content range ', ($mediaHeaders['content-range'] ?? 'missing'),
            '; content length ', ($mediaHeaders['content-length'] ?? 'missing'),
            '; bytes ', is_string($mediaBytes) ? strlen($mediaBytes) : 0, "\n";
        if ($mediaStatus !== 206
            || ($mediaHeaders['access-control-allow-origin'] ?? '') !== 'https://music.yandex.ru'
            || !str_starts_with(strtolower($mediaHeaders['content-type'] ?? ''), 'audio/mpeg')
            || ($mediaHeaders['accept-ranges'] ?? '') !== 'bytes'
            || !str_starts_with($mediaHeaders['content-range'] ?? '', 'bytes 0-1023/')
            || !is_string($mediaBytes) || strlen($mediaBytes) !== 1024) {
            throw new RuntimeException('public_signed_audio_failed');
        }
        echo "HTTPS media Origin, CORS and Range verified; signed URL not logged.\n";
        echo "Internal and public HTTPS authorized resolve + signed audio HEAD passed; analytics disabled.\\n";
        exit(0);
    }

    if ($operation === 'probe' || $operation === 'import') {
        if ($operation === 'import' && $isOn) {
            throw new RuntimeException('import_preconditions_failed');
        }
        $files = [];
        foreach (scandir($staging) ?: [] as $name) {
            // Filesystem basename only; allow the owner's Unicode song names.
            if ($name === '.' || $name === '..' || str_starts_with($name, '.')
                || !preg_match('/\\.(?:mp3|wav)$/iD', $name)) {
                continue;
            }
            $candidate = $staging . '/' . $name;
            if (is_link($candidate)) {
                throw new RuntimeException('staging_symlink_forbidden');
            }
            if (is_file($candidate) && realpath($candidate) === $candidate) {
                $files[] = $candidate;
            }
        }
        if (count($files) !== 1) {
            throw new RuntimeException('staging_requires_exactly_one_valid_audio_file');
        }
        $file = $files[0];
        $size = filesize($file);
        if ($size === false || $size < 1 || $size > (int) $config['max_audio_size']) {
            throw new RuntimeException('invalid_test_audio_size');
        }
        $mime = (new finfo(FILEINFO_MIME_TYPE))->file($file);
        if (!in_array($mime, ['audio/mpeg', 'audio/wav', 'audio/x-wav'], true)) {
            throw new RuntimeException('unsupported_test_audio');
        }
        if ($operation === 'probe') {
            // The private file is streamed over pinned SSH into runner scratch only.
            // Never echo its basename, audio data in logs, or signed URLs.
            $handle = fopen($file, 'rb');
            if ($handle === false) {
                throw new RuntimeException('test_audio_unreadable');
            }
            while (!feof($handle)) {
                $chunk = fread($handle, 65536);
                if ($chunk === false || ($chunk === '' && !feof($handle))) {
                    throw new RuntimeException('test_audio_unreadable');
                }
                echo $chunk;
            }
            fclose($handle);
            exit(0);
        }
        if (($request['confirm_reviewed'] ?? null) !== true || !is_int($request['duration_ms'])
            || $request['duration_ms'] < 1000 || $request['duration_ms'] > 86400000) {
            throw new RuntimeException('import_preconditions_failed');
        }
        $storage = new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
        $pdo = Celikom\Database\Connection::open($config);
        $importer = new Celikom\Application\TestAudioImporter($pdo, $storage, $config['max_audio_size']);
        $id = $importer->import($file, 'yandex', $request['track_id'], $request['duration_ms']);
        $approved = (new Celikom\Repositories\PdoCatalogRepository($pdo))->findActive('yandex', $request['track_id']);
        if ($approved === null || (int) $approved['replacement_id'] !== $id || !$storage->exists($approved['storage_key'])) {
            throw new RuntimeException('import_verification_failed');
        }
        echo 'Reviewed asset imported and approved exact-ID mapping verified. Replacement ID: ', $id, ". Flag remains disabled.\n";
        exit(0);
    }

    if ($operation === 'enable') {
        $storage = new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
        $pdo = Celikom\Database\Connection::open($config);
        $approved = (new Celikom\Repositories\PdoCatalogRepository($pdo))->findActive('yandex', $request['track_id']);
        if ($approved === null || $approved['storage_driver'] !== 'local'
            || !$storage->exists($approved['storage_key'])
            || $storage->getSize($approved['storage_key']) < 1
            || $storage->getSize($approved['storage_key']) > (int) $config['max_audio_size']) {
            throw new RuntimeException('approved_private_audio_not_ready');
        }
    }

    // Replace the exact single feature setting atomically, preserving all secrets.
    $value = $operation === 'enable' ? '1' : '0';
    $updated = preg_replace('/^FEATURE_REPLACEMENTS="[01]"\r?$/m', 'FEATURE_REPLACEMENTS="' . $value . '"', $env, 1, $replaced);
    if ($replaced !== 1 || !is_string($updated)) {
        throw new RuntimeException('feature_update_rejected');
    }
    if ($updated !== $env) {
        $tmp = tempnam($shared, '.feature-');
        if ($tmp === false) {
            throw new RuntimeException('feature_update_rejected');
        }
        try {
            chmod($tmp, 0600);
            if (file_put_contents($tmp, $updated, LOCK_EX) !== strlen($updated) || !rename($tmp, $envPath)) {
                throw new RuntimeException('feature_update_rejected');
            }
        } finally {
            if (is_file($tmp)) {
                unlink($tmp);
            }
        }
    }
    echo 'Replacement feature set to ', $value === '1' ? 'enabled' : 'disabled', "; analytics remains disabled.\n";
} catch (Throwable) {
    fwrite(STDERR, "Private audio operation failed. Inspect preconditions, private staging or server state; secrets were not logged.\n");
    exit(1);
}
