<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

use PDO;

/**
 * Stage 10 foundation: single server-side decision point for access rights.
 * Trial creation is intentionally added separately after schema migration.
 */
final class EntitlementService
{
    public function __construct(private readonly PDO $pdo)
    {
    }

    public function check(int $userId): EntitlementResult
    {
        $query = $this->pdo->prepare(
            'SELECT trial_started_at, trial_ends_at FROM users WHERE id = ? LIMIT 1'
        );
        $query->execute([$userId]);
        $user = $query->fetch(PDO::FETCH_ASSOC);

        if (!$user) {
            return new EntitlementResult(false, 'none', null, 'user_not_found');
        }

        if ($user['trial_ends_at'] !== null && strtotime((string)$user['trial_ends_at'] . ' UTC') > time()) {
            return new EntitlementResult(true, 'trial', (string)$user['trial_ends_at'], 'trial_active');
        }

        return new EntitlementResult(false, 'none', $user['trial_ends_at'] ?: null, 'no_entitlement');
    }
}
