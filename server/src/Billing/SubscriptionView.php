<?php

declare(strict_types=1);

namespace Celikom\Billing;

use Celikom\Entitlement\EntitlementResult;
use Celikom\Entitlement\EntitlementService;
use PDO;

/** Account-scoped read model. No checkout, renewal request or access mutation. */
final class SubscriptionView
{
    public function __construct(private readonly PDO $pdo) {}

    public function forUser(int $userId): array
    {
        $q=$this->pdo->prepare("SELECT s.id,s.plan_key,s.currency,s.amount_minor,s.status,s.cancel_at_period_end,
            MAX(CASE WHEN p.revoked_at IS NULL AND p.valid_from<=UTC_TIMESTAMP(6)
                AND p.valid_until>UTC_TIMESTAMP(6) AND l.user_id=s.user_id AND l.source='subscription'
                AND l.reason='payment_confirmed' AND l.valid_from=p.valid_from AND l.valid_until=p.valid_until
                THEN p.valid_until END) AS paid_until,
            COUNT(p.id) AS payment_count
            FROM subscriptions s LEFT JOIN billing_payments p ON p.subscription_id=s.id
            LEFT JOIN entitlement_ledger l ON l.id=p.ledger_id
            WHERE s.user_id=? GROUP BY s.id ORDER BY s.id DESC LIMIT 100");
        $q->execute([$userId]);$subscriptions=[];
        foreach($q->fetchAll(PDO::FETCH_ASSOC) as $row) {
            $status=$row['paid_until']!==null ? 'active' : ($row['payment_count']>0 ? 'inactive' : $row['status']);
            $subscriptions[]=[
                'plan'=>$row['plan_key'],'currency'=>$row['currency'],'amount_minor'=>(int)$row['amount_minor'],
                'status'=>$status,'renewal_status'=>$row['cancel_at_period_end'] ? 'cancelled' : 'not_confirmed',
                'paid_until'=>$row['paid_until']===null ? null : EntitlementResult::utc($row['paid_until']),
                // A paid period is not proof of the provider's next debit date.
                'next_payment_at'=>null,
            ];
        }
        return ['entitlement'=>(new EntitlementService($this->pdo))->check($userId)->json(),
            'subscriptions'=>$subscriptions,'payments_available'=>false,
            'actions'=>['pay'=>false,'cancel'=>false,'resume'=>false],
            'message'=>'Подключение оплаты готовится'];
    }
}
