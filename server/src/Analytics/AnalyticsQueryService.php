<?php

declare(strict_types=1);

namespace Celikom\Analytics;

final class AnalyticsQueryService
{
    public function __construct(private readonly \PDO $pdo)
    {
    }

    public function aggregateDay(string $date): int
    {
        $parsed = \DateTimeImmutable::createFromFormat('!Y-m-d', $date, new \DateTimeZone('UTC'));
        if ($parsed === false || $parsed->format('Y-m-d') !== $date) {
            throw new \InvalidArgumentException('invalid_aggregate_date');
        }
        $this->pdo->beginTransaction();
        try {
            $delete = $this->pdo->prepare('DELETE FROM analytics_daily_aggregates WHERE aggregate_date = ?');
            $delete->execute([$date]);
            $insert = $this->pdo->prepare('INSERT INTO analytics_daily_aggregates (aggregate_date, schema_version, metric, platform, event_count, installation_count) SELECT ?, schema_version, event_name, platform, COUNT(*), COUNT(DISTINCT installation_hash) FROM analytics_events WHERE occurred_at >= ? AND occurred_at < ? GROUP BY schema_version, event_name, platform');
            $insert->execute([$date, $date . ' 00:00:00', $parsed->modify('+1 day')->format('Y-m-d') . ' 00:00:00']);
            $count = $insert->rowCount();
            $this->pdo->commit();
            return $count;
        } catch (\Throwable $error) {
            $this->pdo->rollBack();
            throw $error;
        }
    }

    public function purge(int $retentionDays): int
    {
        if ($retentionDays < 2 || $retentionDays > 365) {
            throw new \InvalidArgumentException('invalid_retention');
        }
        $statement = $this->pdo->prepare('DELETE FROM analytics_events WHERE occurred_at < ?');
        $statement->execute([gmdate('Y-m-d H:i:s', time() - $retentionDays * 86400)]);
        return $statement->rowCount();
    }
}
