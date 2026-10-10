<?php

declare(strict_types=1);

namespace Celikom\Auth;

use PDO;

final class BearerAuthenticator
{
    public function __construct(private readonly PDO $pdo)
    {
    }

    public function userId(array $headers): ?int
    {
        $authorization = $headers['authorization'] ?? '';
        if (!is_string($authorization) || !str_starts_with($authorization, 'Bearer ')) {
            return null;
        }

        $token = substr($authorization, 7);
        if (!preg_match('/^[0-9a-f]{64}$/D', $token)) {
            return null;
        }

        $stmt = $this->pdo->prepare('SELECT s.user_id FROM user_sessions s JOIN users u ON u.id = s.user_id
            JOIN user_email_security e ON e.user_id = u.id
            WHERE s.access_hash = ? AND s.revoked_at IS NULL AND s.access_expires_at > UTC_TIMESTAMP(6)
              AND u.status = \'active\' AND e.verified_at IS NOT NULL LIMIT 1');
        $stmt->execute([hash('sha256', $token)]);
        $id = $stmt->fetchColumn();

        return $id === false ? null : (int) $id;
    }
}
