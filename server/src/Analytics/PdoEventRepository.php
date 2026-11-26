<?php

declare(strict_types=1);

namespace Celikom\Analytics;

final class PdoEventRepository implements EventRepository
{
    public function __construct(private readonly \PDO $pdo)
    {
    }

    public function insert(array $event): bool
    {
        try {
            $statement = $this->pdo->prepare('INSERT INTO analytics_events (event_id, schema_version, event_name, installation_hash, client_version, platform, occurred_at, properties_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
            $statement->execute([$event['event_id'], 1, $event['event_name'], $event['installation_hash'], $event['client_version'], $event['platform'], $event['occurred_at'], json_encode($event['properties'], JSON_THROW_ON_ERROR)]);
            return true;
        } catch (\PDOException $error) {
            if (($error->errorInfo[1] ?? null) === 1062) {
                return false;
            }
            throw $error;
        }
    }
}
