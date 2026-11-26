<?php

declare(strict_types=1);

namespace Celikom\Billing;

/** No concrete adapter is registered in the live Application in this package. */
interface BillingAdapter
{
    public function name(): string;

    /** Provider owns card handling. Retries use the same server request key. */
    public function createCheckout(int $userId, BillingPlan $plan, string $requestId): CheckoutSession;

    /** Provider confirmation arrives through a verified event, not this response. */
    public function setRenewal(string $subscriptionId, bool $enabled, string $requestId): void;

    /** Must verify exact raw bytes and provider authenticity before normalizing. */
    public function verifyWebhook(string $body, array $headers): BillingEvent;
}
