<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

use PDO;

final class EntitlementLedger
{
    public function __construct(private readonly PDO $pdo) {}

    /** Caller owns the account row lock and transaction. */
    public function recordTrial(int $userId, string $validFrom, string $validUntil): int
    {
        if (!$this->pdo->inTransaction()) {
            throw new \LogicException('trial_transaction_required');
        }
        $insert = $this->pdo->prepare(
            'INSERT INTO entitlement_ledger (user_id, source, reason, valid_from, valid_until)
             VALUES (?, ?, ?, ?, ?)'
        );
        $insert->execute([$userId, 'trial', 'first_activation', $validFrom, $validUntil]);
        return (int)$this->pdo->lastInsertId();
    }
}
