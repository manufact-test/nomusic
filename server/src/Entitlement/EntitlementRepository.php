<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

use PDO;

final class EntitlementRepository
{
    public function __construct(private readonly PDO $pdo)
    {
    }

    public function hasUser(int $userId): bool
    {
        $statement = $this->pdo->prepare('SELECT 1 FROM users WHERE id = ? LIMIT 1');
        $statement->execute([$userId]);
        return $statement->fetchColumn() !== false;
    }
}
