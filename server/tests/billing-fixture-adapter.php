<?php

declare(strict_types=1);

// Test-only adapter. Never autoloaded or registered by Application.
use Celikom\Billing\BillingAdapter;
use Celikom\Billing\BillingPlan;
use Celikom\Billing\BillingEvent;
use Celikom\Billing\CheckoutSession;

final class BillingFixtureAdapter implements BillingAdapter {
    public function __construct(private readonly string $secret) {}
    public function name(): string { return 'fixture'; }
    public function createCheckout(int $userId, BillingPlan $plan, string $requestId): CheckoutSession
    { return new CheckoutSession('checkout-'.$requestId,'https://checkout.example.invalid/session/'.$requestId); }
    public function setRenewal(string $subscriptionId, bool $enabled, string $requestId): void {}
    public function verifyWebhook(string $body, array $headers): BillingEvent
    {
        if (!hash_equals(hash_hmac('sha256',$body,$this->secret),(string)($headers['signature'] ?? ''))) {
            throw new DomainException('invalid_billing_signature');
        }
        $data = json_decode($body,true,32,JSON_THROW_ON_ERROR);
        return new BillingEvent(...$data);
    }
}
