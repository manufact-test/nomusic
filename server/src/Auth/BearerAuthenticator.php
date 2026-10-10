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
        return $this->session($headers)['user_id'] ?? null;
    }

    public function session(array $headers): ?array
    {
        $authorization = $headers['authorization'] ?? '';
        if (!is_string($authorization) || !str_starts_with($authorization, 'Bearer ')) {
            return null;
        }

        $token = substr($authorization, 7);
        if (!preg_match('/^[0-9a-f]{64}$/D', $token)) {
            return null;
        }

        $stmt = $this->pdo->prepare('SELECT s.id AS session_id, s.user_id, s.refresh_expires_at FROM user_sessions s JOIN users u ON u.id = s.user_id
            JOIN user_email_security e ON e.user_id = u.id
            WHERE s.access_hash = ? AND s.revoked_at IS NULL AND s.access_expires_at > UTC_TIMESTAMP(6)
              AND u.status = \'active\' AND e.verified_at IS NOT NULL LIMIT 1');
        $stmt->execute([hash('sha256', $token)]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$row) return null;
        return ['session_id' => (int)$row['session_id'], 'user_id' => (int)$row['user_id'],
            'refresh_expires_at' => $row['refresh_expires_at']];
    }
}
