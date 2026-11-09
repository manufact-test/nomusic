<?php

declare(strict_types=1);

namespace Celikom\Billing;

use PDO;

final class SubscriptionService
{
    public function __construct(private readonly PDO $pdo) {}

    /** Called by server checkout integration, never with client-provided prices. */
    public function registerPending(int $userId, string $provider, string $reference, BillingPlan $plan): int
    {
        self::provider($provider); BillingEvent::reference($reference);
        if ($userId < 1 || $this->pdo->inTransaction()) throw new \InvalidArgumentException('invalid_subscription');
        $this->pdo->beginTransaction();
        try {
            $q = $this->pdo->prepare('SELECT u.status,e.verified_at FROM users u
                LEFT JOIN user_email_security e ON e.user_id=u.id WHERE u.id=? FOR UPDATE');
            $q->execute([$userId]); $user = $q->fetch(PDO::FETCH_ASSOC);
            if (!$user || $user['status'] !== 'active' || $user['verified_at'] === null) {
                throw new \DomainException('subscription_account_unavailable');
            }
            $q = $this->pdo->prepare('SELECT * FROM subscriptions WHERE provider=? AND provider_subscription_id=? FOR UPDATE');
            $q->execute([$provider,$reference]); $existing = $q->fetch(PDO::FETCH_ASSOC);
            if ($existing) {
                if ((int)$existing['user_id'] !== $userId || $existing['plan_key'] !== $plan->key
                    || $existing['currency'] !== $plan->currency || (int)$existing['amount_minor'] !== $plan->amountMinor) {
                    throw new \DomainException('subscription_reference_conflict');
                }
                $id = (int)$existing['id'];
            } else {
                $q = $this->pdo->prepare('INSERT INTO subscriptions
                    (user_id,provider,provider_subscription_id,plan_key,currency,amount_minor) VALUES(?,?,?,?,?,?)');
                $q->execute([$userId,$provider,$reference,$plan->key,$plan->currency,$plan->amountMinor]);
                $id = (int)$this->pdo->lastInsertId();
            }
            $this->pdo->commit(); return $id;
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }

    public static function provider(string $provider): void
    {
        if (!preg_match('/^[a-z][a-z0-9_-]{0,31}$/D', $provider)) throw new \InvalidArgumentException('invalid_billing_provider');
    }
}
