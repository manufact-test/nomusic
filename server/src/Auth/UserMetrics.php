<?php

declare(strict_types=1);

namespace Celikom\Auth;

/** Authenticated starts only: never join anonymous installs by fingerprint. */
final class UserMetrics
{
    public function __construct(private readonly \PDO $pdo) {}

    public function hasAccounts(): bool
    {
        return (int)$this->pdo->query('SELECT COUNT(*) FROM users')->fetchColumn() > 0;
    }

    public function forPeriod(string $start, string $end): array
    {
        $new = $this->count('SELECT COUNT(*) FROM users WHERE created_at >= ? AND created_at < ?', [$start,$end]);
        $first = $this->count('SELECT COUNT(*) FROM users WHERE first_activated_at >= ? AND first_activated_at < ?', [$start,$end]);
        $active = $this->count("SELECT COUNT(DISTINCT user_id) FROM user_auth_events
            WHERE event_name = 'celikom_started' AND created_at >= ? AND created_at < ?", [$start,$end]);
        $returning = $this->count("SELECT COUNT(DISTINCT e.user_id) FROM user_auth_events e
            WHERE e.event_name = 'celikom_started' AND e.created_at >= ? AND e.created_at < ?
            AND EXISTS (SELECT 1 FROM user_auth_events past
                WHERE past.user_id = e.user_id AND past.event_name = 'celikom_started'
                  AND past.created_at < ?)", [$start,$end,$start]);
        return ['new' => $new, 'first' => $first, 'active' => $active, 'returning' => $returning];
    }

    private function count(string $sql, array $params): int
    {
        $select = $this->pdo->prepare($sql);
        $select->execute($params);
        return (int)$select->fetchColumn();
    }
}
