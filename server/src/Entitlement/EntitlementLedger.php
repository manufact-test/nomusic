<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

use PDO;

final class EntitlementLedger
{
    public function __construct(private readonly PDO $pdo)
    {
    }

    public function recordTrial(int $userId, string $validUntil): void
    {
        $insert = $this->pdo->prepare(
            'INSERT INTO entitlement_ledger
                (user_id, source, reason, valid_from, valid_until)
             VALUES (?, ?, ?, UTC_TIMESTAMP(6), ?)'
        );

        $insert->execute([
            $userId,
            'trial',
            'first_activation',
            $validUntil,
        ]);
    }
}
