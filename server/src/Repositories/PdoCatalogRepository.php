<?php

declare(strict_types=1);

namespace Celikom\Repositories;

final class PdoCatalogRepository implements CatalogRepository
{
    private const SELECT = "SELECT r.id AS replacement_id, r.version, a.storage_driver, a.storage_key,
        a.sha256, a.mime_type, a.size_bytes, a.duration_ms FROM track_replacements r
        JOIN tracks t ON t.id = r.track_id JOIN audio_assets a ON a.id = r.audio_asset_id
        WHERE r.status = 'approved' AND r.is_active = 1 AND r.disabled_at IS NULL";

    public function __construct(private readonly \PDO $pdo)
    {
    }

    public function findActive(string $service, string $trackId): ?array
    {
        return $this->one(self::SELECT . ' AND t.service = ? AND t.service_track_id = ?', [$service, $trackId]);
    }

    public function findByReplacement(int $id): ?array
    {
        return $this->one(self::SELECT . ' AND r.id = ?', [$id]);
    }

    private function one(string $sql, array $parameters): ?array
    {
        $statement = $this->pdo->prepare($sql);
        $statement->execute($parameters);
        $row = $statement->fetch(\PDO::FETCH_ASSOC);
        return $row === false ? null : $row;
    }
}
