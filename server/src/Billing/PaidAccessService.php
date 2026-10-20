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
        $q = $this->pdo->prepare("SELECT p.valid_from,p.valid_until,UTC_TIMESTAMP(6) AS database_now
            FROM subscriptions s JOIN billing_payments p ON p.subscription_id=s.id
            JOIN entitlement_ledger l ON l.id=p.ledger_id
            WHERE s.user_id=? AND l.user_id=s.user_id AND l.source='subscription'
                AND l.reason='payment_confirmed' AND l.valid_from=p.valid_from AND l.valid_until=p.valid_until
                AND p.revoked_at IS NULL AND p.valid_from<=UTC_TIMESTAMP(6)");
        $q->execute([$userId]); $until = null;
        $intervals = (new \Celikom\Incident\IncidentService($this->pdo))->intervals();
        foreach ($q->fetchAll(PDO::FETCH_ASSOC) as $row) {
            $effective = \Celikom\Incident\IncidentService::extendedUntil($row['valid_from'],$row['valid_until'],$intervals);
            if ($effective > $row['database_now'] && ($until === null || $effective > $until)) $until = $effective;
        }
        return $until !== null ? EntitlementResult::utc($until) : null;
    }
}
