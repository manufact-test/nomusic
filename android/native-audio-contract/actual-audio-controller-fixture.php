<?php
declare(strict_types=1);

/**
 * Contract-only invocation of ACTUAL, unchanged production AudioController,
 * AudioTokenService, ByteRange and Response implementations. Synthetic bytes
 * and in-memory test repositories only: never opens production storage or DB.
 *
 * Emits only headers, response status, and SHA256 of manufactured test bytes.
 */
$root = dirname(__DIR__, 2);
require $root . '/server/src/Repositories/CatalogRepository.php';
require $root . '/server/src/Storage/StorageAdapter.php';
require $root . '/server/src/Application/AudioTokenService.php';
require $root . '/server/src/Http/Response.php';
require $root . '/server/src/Http/ByteRange.php';
require $root . '/server/src/Http/AudioController.php';

use Celikom\Repositories\CatalogRepository;
use Celikom\Storage\StorageAdapter;
use Celikom\Application\AudioTokenService;
use Celikom\Http\AudioController;
use Celikom\Http\Response;

$payload = str_repeat('0123456789abcdef', 256);
assert(strlen($payload) === 4096);
$row = [
    'replacement_id' => 42,
    'version' => 3,
    'size_bytes' => strlen($payload),
    'mime_type' => 'audio/mpeg',
    'sha256' => hash('sha256', $payload),
    'storage_driver' => 'local',
    'storage_key' => 'owned-ci-audio-bytes',
    'duration_ms' => 180000,
    'gain_db' => 0.0,
];
$catalog = new class($row) implements CatalogRepository {
    public function __construct(private readonly array $row) {}
    public function findActive(string $service, string $trackId): ?array
    {
        return $service === 'yandex' && $trackId === '123' ? $this->row : null;
    }
    public function findByReplacement(int $id): ?array
    {
        return $id === 42 ? $this->row : null;
    }
};
$storage = new class($payload) implements StorageAdapter {
    public function __construct(private readonly string $payload) {}
    public function put(string $key, mixed $source): void { throw new \LogicException('write forbidden'); }
    public function openStream(string $key): mixed
    {
        if ($key !== 'owned-ci-audio-bytes') throw new \LogicException('unexpected key');
        $stream = fopen('php://temp', 'w+b');
        if ($stream === false || fwrite($stream, $this->payload) !== strlen($this->payload)) {
            throw new \RuntimeException('fixture stream failed');
        }
        rewind($stream);
        return $stream;
    }
    public function exists(string $key): bool { return $key === 'owned-ci-audio-bytes'; }
    public function delete(string $key): void { throw new \LogicException('delete forbidden'); }
    public function move(string $from, string $to): void { throw new \LogicException('move forbidden'); }
    public function getSize(string $key): int { return strlen($this->payload); }
    public function getMimeType(string $key): string { return 'audio/mpeg'; }
};
$tokens = new AudioTokenService(str_repeat('own-ci-fixture-key-', 3), 600);
$controller = new AudioController($catalog, $storage, $tokens);
$expires = time() + 240;
$validToken = $tokens->sign(42, 3, $expires);
$etag = '"' . $row['sha256'] . '-3"';

function present(Response $response): array
{
    ob_start();
    try {
        $response->emitBody();
        $body = ob_get_contents();
        if ($body === false) throw new \RuntimeException('capture failed');
    } finally {
        ob_end_clean();
    }
    return [
        'status' => $response->status,
        'headers' => $response->headers,
        'bodyBytes' => strlen($body),
        'bodySha256' => hash('sha256', $body),
    ];
}
$authorized = ['expires' => (string) $expires, 'token' => $validToken];
$out = [
    'real_server_classes_invoked' => ['AudioController', 'AudioTokenService', 'ByteRange', 'Response'],
    'payloadSha256' => $row['sha256'],
    'size' => strlen($payload),
    'etag' => $etag,
    'head' => present($controller->handle('HEAD', 42, $authorized, [])),
    'fullGet' => present($controller->handle('GET', 42, $authorized, [])),
    'byteGet' => present($controller->handle('GET', 42, $authorized,
        ['range' => 'bytes=1024-2047', 'if-range' => $etag])),
    'openEnd' => present($controller->handle('GET', 42, $authorized,
        ['range' => 'bytes=1024-'])),
    'clippedEnd' => present($controller->handle('GET', 42, $authorized,
        ['range' => 'bytes=3000-9999'])),
    'invalidEnd' => present($controller->handle('GET', 42, $authorized,
        ['range' => 'bytes=4096-'])),
    'wrongIfRange' => present($controller->handle('GET', 42, $authorized,
        ['range' => 'bytes=1024-2047', 'if-range' => '"obsolete"'])),
    'wrongToken' => present($controller->handle('GET', 42, [
        'expires' => (string) $expires, 'token' => str_repeat('0', 64)
    ], ['range' => 'bytes=1024-2047'])),
    'unknownSession' => present($controller->handle('GET', 42,
        ['expires' => (string) $expires,
         'token' => $tokens->sign(42, 3, $expires, 17),
         'sid' => '17'], ['range' => 'bytes=1024-2047'])),
];
echo json_encode($out, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES) . PHP_EOL;
