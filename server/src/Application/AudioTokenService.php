<?php

declare(strict_types=1);

namespace Celikom\Application;

final class AudioTokenService
{
    public function __construct(private readonly string $key, public readonly int $ttl = 600)
    {
        if (strlen($key) < 32 || $ttl < 60 || $ttl > 1800) {
            throw new \RuntimeException('audio_signing_not_configured');
        }
    }

    public function sign(int $replacementId, int $version, int $expires): string
    {
        return hash_hmac('sha256', "audio.v1\n$replacementId\n$version\n$expires", $this->key);
    }

    public function valid(int $replacementId, int $version, string $expires, string $token, ?int $now = null): bool
    {
        $now ??= time();
        if (!preg_match('/^\d{1,12}$/D', $expires) || !preg_match('/^[a-f0-9]{64}$/D', $token)) {
            return false;
        }
        $deadline = (int) $expires;
        return $deadline > $now && $deadline <= $now + $this->ttl
            && hash_equals($this->sign($replacementId, $version, $deadline), $token);
    }
}
