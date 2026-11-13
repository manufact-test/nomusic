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

    public function sign(int $replacementId, int $version, int $expires, ?int $sessionId = null): string
    {
        $message = $sessionId === null ? "audio.v1\n$replacementId\n$version\n$expires"
            : "audio.v2\n$replacementId\n$version\n$expires\n$sessionId";
        return hash_hmac('sha256', $message, $this->key);
    }

    /** Variant signature is distinct from the ordinary browser token and binds
     * the exact render digest. Only a fresh session may request this route.
     */
    public function signWindowsGain(int $replacementId, int $version, int $expires, int $sessionId, string $sha256): string
    {
        if ($sessionId < 1 || preg_match('/^[a-f0-9]{64}$/D', $sha256) !== 1)
            throw new \InvalidArgumentException('invalid_windows_gain_signature');
        return hash_hmac('sha256', "audio.windows-gain.v1\n$replacementId\n$version\n$expires\n$sessionId\n$sha256", $this->key);
    }

    public function validWindowsGain(int $replacementId, int $version, string $expires, string $token,
        int $sessionId, string $sha256, ?int $now = null): bool
    {
        $now ??= time();
        if ($sessionId < 1 || preg_match('/^\d{1,12}$/D', $expires) !== 1
            || preg_match('/^[a-f0-9]{64}$/D', $token) !== 1
            || preg_match('/^[a-f0-9]{64}$/D', $sha256) !== 1)
            return false;
        $deadline = (int)$expires;
        return $deadline > $now && $deadline <= $now + $this->ttl &&
            hash_equals($this->signWindowsGain($replacementId, $version, $deadline, $sessionId, $sha256), $token);
    }

    public function valid(int $replacementId, int $version, string $expires, string $token, ?int $now = null, ?int $sessionId = null): bool
    {
        $now ??= time();
        if (!preg_match('/^\d{1,12}$/D', $expires) || !preg_match('/^[a-f0-9]{64}$/D', $token)) {
            return false;
        }
        $deadline = (int) $expires;
        return $deadline > $now && $deadline <= $now + $this->ttl
            && hash_equals($this->sign($replacementId, $version, $deadline, $sessionId), $token);
    }
}
