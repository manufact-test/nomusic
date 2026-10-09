<?php

declare(strict_types=1);

namespace Celikom\Application;

/**
 * Limited per-track moderation presence only. Never returns filenames,
 * submission owner, file hashes, or private media addresses over HTTP.
 */
final class TrackUploadStatusService
{
    public function __construct(private readonly \PDO $pdo) {}

    public function get(string $service, string $trackId): ?array
    {
        if ($service !== 'yandex' || !preg_match('/^[1-9]\d{0,23}$/D', $trackId)) {
            throw new \InvalidArgumentException('invalid_track');
        }
        $stmt = $this->pdo->prepare("SELECT r.id, r.status, a.sha256
            FROM tracks t
            JOIN track_replacements r ON r.track_id = t.id
            JOIN audio_assets a ON a.id = r.audio_asset_id
            WHERE t.service = ? AND t.service_track_id = ? AND r.disabled_at IS NULL
              AND r.status IN ('pending', 'approved')
            ORDER BY CASE WHEN r.status = 'pending' THEN 0 ELSE 1 END, r.id
            LIMIT 1");
        $stmt->execute([$service, $trackId]);
        return $stmt->fetch(\PDO::FETCH_ASSOC) ?: null;
    }

    public function state(string $service, string $trackId): array
    {
        $record = $this->get($service, $trackId);
        return ['status' => $record['status'] ?? 'none'];
    }
}
