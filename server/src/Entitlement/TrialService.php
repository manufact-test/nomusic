<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

use PDO;

/**
 * Stage 10.1: creates the initial trial entitlement after verified activation.
 * Uses server UTC time only. Billing/subscription logic is intentionally outside this service.
 */
final class TrialService
{
    private const TRIAL_SECONDS = 432000; // 5 days

    public function __construct(private readonly PDO $pdo)
    {
    }

    public function activate(int $userId): array
    {
        $this->pdo->beginTransaction();
        try {
            $select = $this->pdo->prepare(
                'SELECT id, trial_started_at, trial_ends_at FROM users WHERE id = ? LIMIT 1 FOR UPDATE'
            );
            $select->execute([$userId]);
            $user = $select->fetch(PDO::FETCH_ASSOC);

            if (!$user) {
                throw new \DomainException('user_not_found');
            }

            if ($user['trial_started_at'] !== null) {
                $this->pdo->commit();
                return [
                    'activated' => false,
                    'trial_ends_at' => $user['trial_ends_at'],
                ];
            }

            $update = $this->pdo->prepare(
                'UPDATE users
                 SET trial_started_at = UTC_TIMESTAMP(6),
                     trial_ends_at = DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 432000 SECOND)
                 WHERE id = ?'
            );
            $update->execute([$userId]);

            $this->pdo->commit();

            return [
                'activated' => true,
                'trial_seconds' => self::TRIAL_SECONDS,
            ];
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) {
                $this->pdo->rollBack();
            }
            throw $error;
        }
    }
}
