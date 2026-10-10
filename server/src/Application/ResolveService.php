<?php

declare(strict_types=1);

namespace Celikom\Application;

use Celikom\Repositories\CatalogRepository;
use Celikom\Storage\StorageAdapter;

final class ResolveService
{
    public function __construct(
        private readonly CatalogRepository $catalog,
        private readonly StorageAdapter $storage,
        private readonly AudioTokenService $tokens,
        private readonly int $positiveTtlSeconds = 120,
        private readonly int $negativeTtlSeconds = 15,
    ) {
    }

    public function resolve(string $service, string $trackId, ?array $access = null): array
    {
        if ($service !== 'yandex' || !preg_match('/^[1-9]\d{0,23}$/D', $trackId)) {
            throw new \InvalidArgumentException('invalid_track');
        }
        $row = $this->catalog->findActive($service, $trackId);
        if ($row === null || $row['storage_driver'] !== 'local' || !$this->storage->exists($row['storage_key'])) {
            return ['found' => false, 'cache_ttl_seconds' => ResolveCachePolicy::negative($this->negativeTtlSeconds)];
        }
        $id = (int) $row['replacement_id'];
        $version = (int) $row['version'];
        $expires = time() + $this->tokens->ttl;
        if ($access !== null) {
            $expires = min($expires, (int)strtotime($access['valid_until']),
                (int)strtotime($access['refresh_expires_at'] . ' UTC'));
            if ($expires <= time()) return ['found' => false, 'cache_ttl_seconds' => 0];
        }
        $sessionId = $access['session_id'] ?? null;
        return [
            'found' => true,
            'replacement_id' => $id,
            'audio_url' => '/api/v1/audio/' . $id . '?token=' . $this->tokens->sign($id, $version, $expires, $sessionId) . '&expires=' . $expires . ($sessionId === null ? '' : '&sid=' . $sessionId),
            'duration_ms' => (int) $row['duration_ms'],
            'version' => $version,
            'expires_at' => $expires,
            'cache_ttl_seconds' => min(ResolveCachePolicy::positive($this->positiveTtlSeconds, $this->tokens->ttl), max(0, $expires - time())),
        ];
    }
}
