<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';

use Celikom\Application;
use Celikom\Application\AudioTokenService;
use Celikom\Analytics\AnalyticsEventService;
use Celikom\Analytics\EventRepository;
use Celikom\Repositories\CatalogRepository;
use Celikom\Storage\LocalStorageAdapter;

function expect(bool $condition, string $message): void
{
    if (!$condition) {
        throw new RuntimeException($message);
    }
}
function run(string $name, Closure $test): void
{
    $test();
    fwrite(STDOUT, "PASS $name\n");
}
function bytes(Celikom\Http\Response $response): string
{
    ob_start();
    $response->emitBody();
    return (string) ob_get_clean();
}
$config = require dirname(__DIR__) . '/config/app.php';
$config['api_enabled'] = true;
$config['analytics_enabled'] = true;
$config['test_api_token'] = str_repeat('test-', 8);
$config['audio_signing_key'] = str_repeat('signing-test-', 4);
$config['analytics_privacy_key'] = str_repeat('privacy-test-', 4);
$auth = ['Authorization' => 'Bearer ' . $config['test_api_token']];
$directory = sys_get_temp_dir() . '/celikom-unit-' . bin2hex(random_bytes(8));
$storage = new LocalStorageAdapter($directory);
$fixture = fopen('php://temp', 'w+b');
fwrite($fixture, '0123456789abcdef');
rewind($fixture);
$storage->put('audio/fixture.mp3', $fixture);
fclose($fixture);
$catalog = new class implements CatalogRepository {
    public bool $throw = false;
    public ?array $row = [
        'replacement_id' => 7, 'version' => 2, 'storage_driver' => 'local',
        'storage_key' => 'audio/fixture.mp3', 'sha256' => 'fixture-sha',
        'mime_type' => 'audio/mpeg', 'size_bytes' => 16, 'duration_ms' => 201000,
    ];
    public function findActive(string $service, string $trackId): ?array
    {
        if ($this->throw) {
            throw new RuntimeException('private/db/path password=should-not-leak');
        }
        return $trackId === '1944599' ? $this->row : null;
    }
    public function findByReplacement(int $id): ?array
    {
        return $id === 7 ? $this->row : null;
    }
};
$events = new class implements EventRepository {
    public array $events = [];
    public function insert(array $event): bool
    {
        if (isset($this->events[$event['event_id']])) {
            return false;
        }
        $this->events[$event['event_id']] = $event;
        return true;
    }
};
$analytics = new AnalyticsEventService($events, $config['analytics_privacy_key']);
$app = new Application($config, $catalog, $storage, $analytics);
$tokens = new AudioTokenService($config['audio_signing_key']);
$expires = time() + 600;
$query = ['expires' => (string) $expires, 'token' => $tokens->sign(7, 2, $expires)];

try {
    run('versioned health/config and unknown routes', function () use ($app): void {
        expect($app->handle('GET', '/api/v1/health')->status === 200, 'Health');
        $config = json_decode($app->handle('GET', '/api/v1/config')->body, true, flags: JSON_THROW_ON_ERROR);
        expect($config['api_version'] === 1 && $config['upload_enabled'] === false, 'Config contract');
        expect($app->handle('GET', '/missing')->status === 404, 'Unknown route');
    });
    run('resolve private access, exact ID, found/not found and no filesystem exposure', function () use ($app, $auth): void {
        expect($app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => '1944599'])->status === 401, 'Anonymous catalog');
        $response = $app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => '1944599'], $auth);
        $data = json_decode($response->body, true, flags: JSON_THROW_ON_ERROR);
        expect($data['found'] && $data['replacement_id'] === 7, 'Found approved mapping');
        expect(!str_contains($response->body, 'storage_key') && !str_contains($response->body, 'fixture.mp3'), 'No private path');
        $missing = json_decode($app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => '999'], $auth)->body, true);
        expect($missing['found'] === false, 'Negative resolve');
        foreach (['0', '001', '1 OR 1=1', '-1', str_repeat('1', 25)] as $id) {
            expect($app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => $id], $auth)->status === 400, 'Invalid ID');
        }
        expect($app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => ['1']], $auth)->status === 400, 'Array ID');
    });
    run('SQL/connection errors become safe 503', function () use ($app, $catalog, $auth): void {
        $catalog->throw = true;
        $response = $app->handle('GET', '/api/v1/resolve', ['service' => 'yandex', 'track_id' => '1944599'], $auth);
        $catalog->throw = false;
        expect($response->status === 503 && $response->body === '{"error":"service_unavailable"}', 'Safe error');
    });
    run('whole audio and HEAD', function () use ($app, $query): void {
        $response = $app->handle('GET', '/api/v1/audio/7', $query);
        expect($response->status === 200 && bytes($response) === '0123456789abcdef', 'Whole body');
        $head = $app->handle('HEAD', '/api/v1/audio/7', $query, ['Range' => 'bytes=2-4']);
        expect($head->status === 200 && bytes($head) === '' && $head->headers['Content-Length'] === '16', 'HEAD');
    });
    foreach (['bytes=0-3' => '0123', 'bytes=5-8' => '5678', 'bytes=15-' => 'f', 'bytes=-3' => 'def', 'bytes=12-999' => 'cdef', 'bytes=-999' => '0123456789abcdef'] as $range => $expected) {
        run('Range ' . $range, function () use ($app, $query, $range, $expected): void {
            $response = $app->handle('GET', '/api/v1/audio/7', $query, ['Range' => $range]);
            expect($response->status === 206 && bytes($response) === $expected, 'Range body');
            expect($response->headers['Content-Length'] === (string) strlen($expected), 'Range length');
            expect(isset($response->headers['Content-Range']), 'Range representation');
        });
    }
    run('malformed/unsatisfiable/multiple ranges', function () use ($app, $query): void {
        foreach (['bytes=16-', 'bytes=5-2', 'bytes=-0', 'bytes=-', 'bytes=0-1,3-4', 'items=0-1', 'bytes=99999999999999999999999-'] as $range) {
            $response = $app->handle('GET', '/api/v1/audio/7', $query, ['Range' => $range]);
            expect($response->status === 416 && $response->headers['Content-Range'] === 'bytes */16' && bytes($response) === '', '416');
        }
    });
    run('If-Range mismatch returns whole current representation', function () use ($app, $query): void {
        $response = $app->handle('GET', '/api/v1/audio/7', $query, ['Range' => 'bytes=4-5', 'If-Range' => '"old"']);
        expect($response->status === 200 && strlen(bytes($response)) === 16, 'If-Range');
    });
    run('invalid/expired/version-revoked signatures', function () use ($app, $query, $tokens): void {
        expect($app->handle('GET', '/api/v1/audio/7', ['expires' => $query['expires'], 'token' => str_repeat('a', 64)])->status === 403, 'Invalid token');
        $old = time() - 1;
        expect($app->handle('GET', '/api/v1/audio/7', ['expires' => (string) $old, 'token' => $tokens->sign(7, 2, $old)])->status === 403, 'Expired token');
        expect($app->handle('GET', '/api/v1/audio/7', ['expires' => $query['expires'], 'token' => $tokens->sign(7, 1, (int) $query['expires'])])->status === 403, 'Version binding');
    });
    run('missing/disabled mapping and missing storage object', function () use ($app, $query, $catalog, $storage): void {
        expect($app->handle('GET', '/api/v1/audio/8', $query)->status === 404, 'Missing mapping');
        $row = $catalog->row;
        $catalog->row = null;
        expect($app->handle('GET', '/api/v1/audio/7', $query)->status === 404, 'Disabled mapping');
        $catalog->row = $row;
        $storage->delete('audio/fixture.mp3');
        expect($app->handle('GET', '/api/v1/audio/7', $query)->status === 404, 'Missing object');
    });
    run('storage traversal and symlink escape are rejected', function () use ($storage, $directory): void {
        foreach (['../x', 'audio/../x', '/tmp/x', 'audio//x', 'php://filter', "audio\\x"] as $key) {
            try {
                $storage->exists($key);
                throw new RuntimeException('Traversal accepted');
            } catch (InvalidArgumentException) {
            }
        }
        symlink(sys_get_temp_dir(), $directory . '/linked');
        try {
            $storage->exists('linked/escape');
            throw new RuntimeException('Symlink accepted');
        } catch (InvalidArgumentException) {
        }
        unlink($directory . '/linked');
    });
    $batch = [
        'schema_version' => 1, 'installation_id' => '00000000-0000-4000-8000-000000000001',
        'client_version' => '0.4.0', 'platform' => 'chromium', 'events' => [[
            'event_id' => '00000000-0000-4000-8000-000000000002',
            'event_name' => 'celikom_started', 'occurred_at' => gmdate('Y-m-d\TH:i:s\Z'), 'properties' => [],
        ]],
    ];
    run('analytics safe partial retry and deduplication', function () use ($analytics, $events, $batch): void {
        expect($analytics->batch($batch)['results'][0]['status'] === 'accepted', 'Accepted');
        expect($analytics->batch($batch)['results'][0]['status'] === 'duplicate', 'Duplicate');
        expect(count($events->events) === 1, 'One event');
        $stored = array_values($events->events)[0];
        expect($stored['installation_hash'] !== $batch['installation_id'] && !isset($stored['installation_id']), 'Pseudonymous storage');
        $retry = $batch;
        $retry['events'][] = ['event_id' => '00000000-0000-4000-8000-000000000003', 'event_name' => 'subscription_started', 'occurred_at' => gmdate('Y-m-d\TH:i:s\Z'), 'properties' => []];
        $retry['events'][] = ['event_id' => '00000000-0000-4000-8000-000000000004', 'event_name' => 'replacement_started', 'occurred_at' => gmdate('Y-m-d\TH:i:s\Z'), 'properties' => ['audio_url' => 'private', 'track_id' => '123']];
        $result = $analytics->batch($retry);
        expect(array_column($result['results'], 'status') === ['duplicate', 'rejected', 'rejected'], 'Partial safe retry');
    });
    run('analytics HTTP type/bounds/feature gate', function () use ($app, $auth, $batch, $config, $catalog, $storage, $analytics): void {
        $headers = $auth + ['Content-Type' => 'application/json'];
        expect($app->handle('POST', '/api/v1/events/batch', headers: $headers, body: json_encode($batch))->status === 202, 'Batch endpoint');
        expect($app->handle('POST', '/api/v1/events/batch', headers: $headers, body: '{')->status === 400, 'JSON');
        expect($app->handle('POST', '/api/v1/events/batch', headers: $auth, body: '{}')->status === 415, 'Type');
        expect($app->handle('POST', '/api/v1/events/batch', headers: $headers, body: str_repeat(' ', 65537))->status === 413, 'Bounded body');
        $config['analytics_enabled'] = false;
        expect((new Application($config, $catalog, $storage, $analytics))->handle('POST', '/api/v1/events/batch', headers: $headers, body: '{}')->status === 503, 'Disabled by default');
    });
} finally {
    foreach (glob($directory . '/audio/*') ?: [] as $file) {
        unlink($file);
    }
    rmdir($directory . '/audio');
    rmdir($directory);
}
fwrite(STDOUT, "CELIKOM PHP unit contracts passed.\n");
