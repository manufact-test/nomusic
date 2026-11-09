<?php

declare(strict_types=1);

namespace Celikom\Application;

/** Database-backed fixed hour buckets, never dependent on per-process memory. */
final class UploadRateLimiter
{
    public function __construct(private readonly \PDO $pdo) {}

    public function check(string $identity, string $operation, int $limit): bool
    {
        if (!in_array($operation, ['upload', 'track_request'], true) || $limit < 1 ||
            !preg_match('/^[a-f0-9]{64}$/D', $identity)) {
            throw new \InvalidArgumentException('invalid_rate_limit');
        }
        $bucket = intdiv(time(), 3600) * 3600;
        $query = $this->pdo->prepare('INSERT INTO upload_rate_buckets (identity_hash, window_start, operation, attempts)
            VALUES (?, ?, ?, 1) ON DUPLICATE KEY UPDATE attempts = attempts + 1');
        $query->execute([$identity, $bucket, $operation]);
        $query = $this->pdo->prepare('SELECT attempts FROM upload_rate_buckets
            WHERE identity_hash = ? AND window_start = ? AND operation = ?');
        $query->execute([$identity, $bucket, $operation]);
        return (int) $query->fetchColumn() <= $limit;
    }
}
