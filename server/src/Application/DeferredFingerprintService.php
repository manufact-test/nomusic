<?php

declare(strict_types=1);

namespace Celikom\Application;

final class DeferredFingerprintService implements AudioFingerprintService
{
    public function __construct(private readonly \PDO $pdo) {}

    public function schedule(int $assetId): void
    {
        if ($assetId < 1) {
            throw new \InvalidArgumentException('invalid_fingerprint_asset');
        }
        $stmt = $this->pdo->prepare("INSERT IGNORE INTO audio_fingerprint_jobs (audio_asset_id, status) VALUES (?, 'pending')");
        $stmt->execute([$assetId]);
    }
}
