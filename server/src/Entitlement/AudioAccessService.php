<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

use PDO;

/** A signed URL is scoped to one independent session and rechecked on every Range. */
final class AudioAccessService
{
    public function __construct(private readonly PDO $pdo) {}

    public function allowed(int $sessionId): bool
    {
        $q = $this->pdo->prepare('SELECT user_id FROM user_sessions
            WHERE id = ? AND revoked_at IS NULL AND refresh_expires_at > UTC_TIMESTAMP(6)');
        $q->execute([$sessionId]);
        $id = $q->fetchColumn();
        return $id !== false && (new EntitlementService($this->pdo))->check((int)$id)->allowed;
    }
}
