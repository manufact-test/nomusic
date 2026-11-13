<?php

declare(strict_types=1);

namespace Celikom\Billing;

final readonly class CheckoutSession
{
    public function __construct(public string $id, public string $url, public ?string $subscriptionId = null)
    {
        BillingEvent::reference($id);
        if ($subscriptionId !== null) BillingEvent::reference($subscriptionId);
        $parts = parse_url($url);
        if (!$parts || ($parts['scheme'] ?? '') !== 'https' || empty($parts['host'])
            || isset($parts['user']) || isset($parts['pass']) || strlen($url) > 4096) {
            throw new \InvalidArgumentException('invalid_checkout_url');
        }
        // Concrete adapters additionally constrain URLs to their provider hosts.
    }
}
