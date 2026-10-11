<?php

declare(strict_types=1);

namespace Celikom\Billing;

use Celikom\Entitlement\EntitlementResult;
use PDO;

final class PaidAccessService
{
    public function __construct(private readonly PDO $pdo) {}

    /** Payment + its exact immutable grant must agree; cancellation keeps paid time. */
    public function validUntil(int $userId): ?string
    {
        $q = $this->pdo->prepare("SELECT MAX(p.valid_until)
            FROM subscriptions s JOIN billing_payments p ON p.subscription_id=s.id
            JOIN entitlement_ledger l ON l.id=p.ledger_id
            WHERE s.user_id=? AND l.user_id=s.user_id AND l.source='subscription'
                AND l.reason='payment_confirmed' AND l.valid_from=p.valid_from AND l.valid_until=p.valid_until
                AND p.revoked_at IS NULL AND p.valid_from<=UTC_TIMESTAMP(6) AND p.valid_until>UTC_TIMESTAMP(6)");
        $q->execute([$userId]); $until = $q->fetchColumn();
        return is_string($until) ? EntitlementResult::utc($until) : null;
    }
}
