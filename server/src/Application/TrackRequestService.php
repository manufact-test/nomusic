<?php

declare(strict_types=1);

namespace Celikom\Application;

final class TrackRequestService
{
    public function __construct(private readonly \PDO $pdo) {}

    /** @param array<string, mixed> $fields */
    public function submit(array $fields, string $uploaderHash): array
    {
        $service = $fields['service'] ?? null;
        $trackId = $fields['track_id'] ?? null;
        if ($service !== 'yandex' || !is_string($trackId)
            || !preg_match('/^[1-9]\d{0,23}$/D', $trackId)
            || !preg_match('/^[a-f0-9]{64}$/D', $uploaderHash)) {
            throw new \InvalidArgumentException('invalid_track_request');
        }
        $metadata = [];
        foreach (['artist', 'title'] as $field) {
            $value = $fields[$field] ?? '';
            if (!is_string($value) || strlen($value) > 240 || !preg_match('//u', $value)
                || preg_match('/[\x00-\x1F]/', $value)) throw new \InvalidArgumentException('invalid_track_request');
            $metadata[] = trim($value);
        }
        $stmt = $this->pdo->prepare("INSERT INTO track_requests
            (service, service_track_id, uploader_hash, artist, title, status)
            VALUES (?, ?, ?, ?, ?, 'pending') ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)");
        $stmt->execute([$service, $trackId, $uploaderHash, ...$metadata]);
        return ['status' => 'pending', 'request_id' => (int) $this->pdo->lastInsertId()];
    }
}
