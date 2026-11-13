<?php

declare(strict_types=1);

namespace Celikom\Billing;

final readonly class BillingPlan
{
    public function __construct(public string $key, public string $currency, public int $amountMinor)
    {
        if (!preg_match('/^[a-z0-9_-]{1,64}$/D', $key) || !preg_match('/^[A-Z]{3}$/D', $currency)
            || $amountMinor < 1 || $amountMinor > 100000000) throw new \InvalidArgumentException('invalid_billing_plan');
    }
}
