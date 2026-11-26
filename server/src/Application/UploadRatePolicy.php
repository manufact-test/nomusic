<?php
declare(strict_types=1);

namespace Celikom\Application;

final class UploadRatePolicy
{
    /* Only the two existing verified administrative identities receive bulk quotas. */
    private const BULK_IDENTITIES = [
        '18e9af33bc55e691582e0495d6f9024611649a3342742ec7569cd565e28af572',
        '50bc7e488885f21b0af751f8e2ed3bc622d3bc097c6541817c9ef742cdf7777e'
    ];

    public static function limitsForVerifiedHash(?string $hash): array
    {
        $bulk=$hash!==null && in_array($hash,self::BULK_IDENTITIES,true);
        return $bulk ? ['account'=>500,'device'=>1000,'ip'=>3000,'bulk'=>true]
            : ['account'=>10,'device'=>20,'ip'=>60,'bulk'=>false];
    }

    public static function forAccount(\PDO $pdo, int $userId): array
    {
        /* Never trust an email, role, promo or identity hash supplied by the client. */
        $q=$pdo->prepare("SELECT u.email FROM users u JOIN user_email_security e ON e.user_id=u.id
            WHERE u.id=? AND u.status='active' AND e.verified_at IS NOT NULL LIMIT 1");
        $q->execute([$userId]); $email=$q->fetchColumn();
        return self::limitsForVerifiedHash(is_string($email)?hash('sha256',strtolower(trim($email))):null);
    }
}
