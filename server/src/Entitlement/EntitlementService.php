<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

use PDO;

/** Read-only decision on the database clock. Paid source is opt-in until provider acceptance. */
final class EntitlementService
{
    public function __construct(private readonly PDO $pdo, private readonly bool $billingEnabled = false) {}

    public function check(int $userId): EntitlementResult
    {
        $query = $this->pdo->prepare(
            "SELECT u.status, e.verified_at, t.valid_from, t.valid_until, UTC_TIMESTAMP(6) AS database_now,
                (t.valid_from <= UTC_TIMESTAMP(6) AND t.valid_until > UTC_TIMESTAMP(6)) AS trial_active,
                (l.user_id = u.id AND l.source = 'trial' AND l.reason = 'first_activation'
                 AND l.valid_from = t.valid_from AND l.valid_until = t.valid_until) AS ledger_matches
             FROM users u
             LEFT JOIN user_email_security e ON e.user_id = u.id
             LEFT JOIN account_trials t ON t.user_id = u.id
             LEFT JOIN entitlement_ledger l ON l.id = t.ledger_id
             WHERE u.id = ?"
        );
        $query->execute([$userId]);
        $user = $query->fetch(PDO::FETCH_ASSOC);
        if (!$user) return new EntitlementResult(false, 'none', null, 'user_not_found');
        if ($user['status'] !== 'active') return new EntitlementResult(false, 'none', null, 'account_disabled');
        if ($user['verified_at'] === null) return new EntitlementResult(false, 'none', null, 'email_unverified');
        $incidents = new \Celikom\Incident\IncidentService($this->pdo);
        $incident = $incidents->state()['active'];
        if ($this->billingEnabled) {
            $paidUntil = (new \Celikom\Billing\PaidAccessService($this->pdo))->validUntil($userId);
            if ($paidUntil !== null) return new EntitlementResult(!$incident, 'subscription', $paidUntil, $incident ? 'service_incident' : 'subscription_active');
        }
        if ($user['valid_until'] === null) return new EntitlementResult(false, 'none', null, 'trial_not_started');
        if (!(bool)$user['ledger_matches']) return new EntitlementResult(false, 'none', null, 'entitlement_inconsistent');
        $effective = $incidents->validUntil($user['valid_from'], $user['valid_until']);
        $until = EntitlementResult::utc($effective);
        $active = $user['valid_from'] <= $user['database_now'] && $effective > $user['database_now'];
        if ($incident && $active) return new EntitlementResult(false, 'trial', $until, 'service_incident');
        return $active
            ? new EntitlementResult(true, 'trial', $until, 'trial_active')
            : new EntitlementResult(false, 'trial', $until, 'trial_inactive');
    }
}
