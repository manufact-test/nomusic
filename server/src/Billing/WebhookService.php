<?php

declare(strict_types=1);

namespace Celikom\Billing;

use PDO;

/** Atomic canonical events, money journal and exact paid-period entitlement. */
final class WebhookService
{
    public function __construct(private readonly PDO $pdo, private readonly BillingAdapter $adapter) {}

    public function handle(string $body, array $headers): array
    {
        if (strlen($body) > 65536 || $this->pdo->inTransaction()) throw new \InvalidArgumentException('invalid_billing_request');
        // Verification also applies to duplicates; an untrusted retry gets no acknowledgement.
        $event = $this->adapter->verifyWebhook($body,$headers);
        $provider = $this->adapter->name(); SubscriptionService::provider($provider);
        $fingerprint = hash('sha256',json_encode($event,JSON_THROW_ON_ERROR));
        $this->pdo->beginTransaction();
        try {
            $q = $this->pdo->prepare('SELECT id,user_id FROM subscriptions WHERE provider=? AND provider_subscription_id=?');
            $q->execute([$provider,$event->subscriptionId]); $identity = $q->fetch(PDO::FETCH_ASSOC);
            if (!$identity) throw new \DomainException('subscription_not_received'); // Retry/reconcile after checkout binding.
            // Same account-first lock order as trial activation, across independent devices/subscriptions.
            $q = $this->pdo->prepare('SELECT id FROM users WHERE id=? FOR UPDATE');
            $q->execute([$identity['user_id']]);
            if (!$q->fetchColumn()) throw new \DomainException('subscription_user_missing');
            $q = $this->pdo->prepare('SELECT * FROM subscriptions WHERE id=? FOR UPDATE');
            $q->execute([$identity['id']]); $subscription = $q->fetch(PDO::FETCH_ASSOC);
            $q = $this->pdo->prepare('SELECT id,subscription_id,event_sha256 FROM billing_events WHERE provider=? AND provider_event_id=? FOR UPDATE');
            $q->execute([$provider,$event->id]); $old = $q->fetch(PDO::FETCH_ASSOC);
            if ($old) {
                if ((int)$old['subscription_id'] !== (int)$subscription['id'] || !hash_equals($old['event_sha256'],$fingerprint)) {
                    throw new \DomainException('billing_event_conflict');
                }
                $this->pdo->commit(); return ['ok'=>true,'duplicate'=>true];
            }
            $q = $this->pdo->prepare('INSERT INTO billing_events
                (subscription_id,provider,provider_event_id,payload_sha256,event_sha256,event_type,occurred_at)
                VALUES(?,?,?,?,?,?,?)');
            $q->execute([$subscription['id'],$provider,$event->id,hash('sha256',$body),$fingerprint,$event->type,$event->occurredAt]);
            $eventId = (int)$this->pdo->lastInsertId();
            if ($event->type === 'paid') $this->paid($subscription,$event,$eventId,$provider);
            elseif ($event->type === 'refund' || $event->type === 'chargeback') $this->adjust($subscription,$event,$eventId,$provider);
            elseif ($event->type === 'failed') $this->paymentState($subscription,$event,'past_due');
            else $this->renewalState($subscription,$event);
            $this->pdo->commit(); return ['ok'=>true,'duplicate'=>false];
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }

    private function paid(array $subscription, BillingEvent $event, int $eventId, string $provider): void
    {
        if ($event->currency !== $subscription['currency'] || $event->amountMinor !== (int)$subscription['amount_minor']) {
            throw new \DomainException('billing_quote_mismatch');
        }
        $q = $this->pdo->prepare('SELECT * FROM billing_payments WHERE provider=? AND provider_payment_id=? FOR UPDATE');
        $q->execute([$provider,$event->paymentId]); $existing = $q->fetch(PDO::FETCH_ASSOC);
        if ($existing) {
            if ((int)$existing['subscription_id'] !== (int)$subscription['id'] || (int)$existing['amount_minor'] !== $event->amountMinor
                || $existing['currency'] !== $event->currency || $existing['valid_from'] !== $event->periodStart
                || $existing['valid_until'] !== $event->periodEnd) throw new \DomainException('billing_payment_conflict');
            // A second event for the same charge cannot grant again, un-revoke or reset status.
            return;
        }
        $q = $this->pdo->prepare("INSERT INTO entitlement_ledger (user_id,source,reason,valid_from,valid_until)
            VALUES(?,'subscription','payment_confirmed',?,?)");
        $q->execute([$subscription['user_id'],$event->periodStart,$event->periodEnd]);
        $ledger = (int)$this->pdo->lastInsertId();
        $q = $this->pdo->prepare('INSERT INTO billing_payments
            (subscription_id,event_id,ledger_id,provider,provider_payment_id,amount_minor,currency,valid_from,valid_until)
            VALUES(?,?,?,?,?,?,?,?,?)');
        $q->execute([$subscription['id'],$eventId,$ledger,$provider,$event->paymentId,$event->amountMinor,$event->currency,$event->periodStart,$event->periodEnd]);
        $this->paymentState($subscription,$event,'active');
    }

    private function paymentState(array $subscription, BillingEvent $event, string $state): void
    {
        // Stale failures cannot override newer successful renewal. At the same
        // provider timestamp success wins; this status never grants access itself.
        $last = $subscription['payment_event_at'];
        if ($last !== null && ($event->occurredAt < $last || ($event->occurredAt === $last && $state !== 'active'))) return;
        $q = $this->pdo->prepare('UPDATE subscriptions SET status=?,payment_event_at=? WHERE id=?');
        $q->execute([$state,$event->occurredAt,$subscription['id']]);
    }

    private function renewalState(array $subscription, BillingEvent $event): void
    {
        $cancel = $event->type === 'renewal_cancelled';
        $last = $subscription['renewal_event_at'];
        // Cancel wins timestamp ties; only a strictly newer explicit resume enables renewal.
        if ($last !== null && ($event->occurredAt < $last || ($event->occurredAt === $last && !$cancel))) return;
        $q = $this->pdo->prepare('UPDATE subscriptions SET cancel_at_period_end=?,renewal_event_at=? WHERE id=?');
        $q->execute([(int)$cancel,$event->occurredAt,$subscription['id']]);
    }

    private function adjust(array $subscription, BillingEvent $event, int $eventId, string $provider): void
    {
        $q = $this->pdo->prepare('SELECT * FROM billing_payments WHERE provider=? AND provider_payment_id=? FOR UPDATE');
        $q->execute([$provider,$event->paymentId]); $payment = $q->fetch(PDO::FETCH_ASSOC);
        if (!$payment) throw new \DomainException('payment_not_received'); // Do not consume early refund; retry after charge.
        if ((int)$payment['subscription_id'] !== (int)$subscription['id'] || $payment['currency'] !== $event->currency) {
            throw new \DomainException('billing_adjustment_mismatch');
        }
        $q = $this->pdo->prepare('SELECT * FROM billing_adjustments WHERE provider=? AND provider_adjustment_id=? FOR UPDATE');
        $q->execute([$provider,$event->adjustmentId]); $existing = $q->fetch(PDO::FETCH_ASSOC);
        if ($existing) {
            if ((int)$existing['payment_id'] !== (int)$payment['id'] || $existing['kind'] !== $event->type
                || (int)$existing['amount_minor'] !== $event->amountMinor) throw new \DomainException('billing_adjustment_conflict');
            return;
        }
        // A locking read must see refunds committed while waiting for the account
        // lock, even under MySQL REPEATABLE READ. A snapshot SUM could over-refund.
        $q = $this->pdo->prepare('SELECT amount_minor FROM billing_adjustments WHERE payment_id=? FOR UPDATE');
        $q->execute([$payment['id']]); $total = $event->amountMinor;
        foreach ($q->fetchAll(PDO::FETCH_COLUMN) as $amount) $total += (int)$amount;
        if ($total > (int)$payment['amount_minor']) throw new \DomainException('billing_adjustment_exceeds_payment');
        $q = $this->pdo->prepare('INSERT INTO billing_adjustments(payment_id,event_id,provider,provider_adjustment_id,kind,amount_minor)
            VALUES(?,?,?,?,?,?)');
        $q->execute([$payment['id'],$eventId,$provider,$event->adjustmentId,$event->type,$event->amountMinor]);
        // Full refund or any chargeback revokes only this charge, never another paid period or trial.
        if ($total === (int)$payment['amount_minor'] || $event->type === 'chargeback') {
            $q = $this->pdo->prepare('UPDATE billing_payments SET revoked_at=COALESCE(revoked_at,UTC_TIMESTAMP(6)) WHERE id=?');
            $q->execute([$payment['id']]);
        }
    }
}
