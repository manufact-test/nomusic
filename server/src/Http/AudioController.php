<?php

declare(strict_types=1);

namespace Celikom\Http;

use Celikom\Application\AudioTokenService;
use Celikom\Repositories\CatalogRepository;
use Celikom\Storage\StorageAdapter;

final class AudioController
{
    public function __construct(private readonly CatalogRepository $catalog, private readonly StorageAdapter $storage, private readonly AudioTokenService $tokens)
    {
    }

    public function handle(string $method, int $id, array $query, array $headers): Response
    {
        $row = $this->catalog->findByReplacement($id);
        if ($row === null) {
            return Response::json(404, ['error' => 'audio_not_found']);
        }
        if (!$this->tokens->valid($id, (int) $row['version'], is_string($query['expires'] ?? null) ? $query['expires'] : '', is_string($query['token'] ?? null) ? $query['token'] : '')) {
            return Response::json(403, ['error' => 'invalid_audio_token']);
        }
        if ($row['storage_driver'] !== 'local' || !$this->storage->exists($row['storage_key'])) {
            return Response::json(404, ['error' => 'audio_not_found']);
        }
        $size = $this->storage->getSize($row['storage_key']);
        if ($size <= 0 || $size !== (int) $row['size_bytes'] || !in_array($row['mime_type'], ['audio/mpeg', 'audio/wav', 'audio/x-wav'], true)) {
            return Response::json(404, ['error' => 'audio_not_found']);
        }
        $etag = '"' . $row['sha256'] . '-' . $row['version'] . '"';
        $responseHeaders = ['Content-Type' => $row['mime_type'], 'Accept-Ranges' => 'bytes', 'ETag' => $etag, 'Cache-Control' => 'private, no-store', 'Content-Length' => (string) $size];
        $start = 0;
        $end = $size - 1;
        $status = 200;
        // RFC 9110: Range applies to GET. HEAD returns full representation headers.
        if ($method === 'GET' && isset($headers['range']) && (!isset($headers['if-range']) || $headers['if-range'] === $etag)) {
            try {
                [$start, $end] = ByteRange::parse($headers['range'], $size);
            } catch (\InvalidArgumentException) {
                return new Response(416, ['Content-Range' => 'bytes */' . $size, 'Accept-Ranges' => 'bytes', 'Content-Length' => '0', 'Cache-Control' => 'no-store']);
            }
            $status = 206;
            $responseHeaders['Content-Range'] = "bytes $start-$end/$size";
            $responseHeaders['Content-Length'] = (string) ($end - $start + 1);
        }
        if ($method === 'HEAD') {
            return new Response($status, $responseHeaders);
        }
        $stream = $this->storage->openStream($row['storage_key']);
        if (fseek($stream, $start) !== 0) {
            fclose($stream);
            throw new \RuntimeException('storage_read_failed');
        }
        $length = $end - $start + 1;
        return new Response($status, $responseHeaders, stream: static function () use ($stream, $length): void {
            $remaining = $length;
            try {
                while ($remaining > 0 && !connection_aborted()) {
                    $chunk = fread($stream, min(65536, $remaining));
                    if ($chunk === false || $chunk === '') {
                        break;
                    }
                    echo $chunk;
                    $remaining -= strlen($chunk);
                }
            } finally {
                fclose($stream);
            }
        });
    }
}
