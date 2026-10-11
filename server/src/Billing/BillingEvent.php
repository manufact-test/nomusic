<?php

declare(strict_types=1);

namespace Celikom\Billing;

/** Trusted adapter output, never deserialized directly from a customer request. */
final readonly class BillingEvent
{
    public function __construct(
        public string $id,
        public string $subscriptionId,
        public string $type,
        public string $occurredAt,
        public ?string $paymentId = null,
        public ?string $periodStart = null,
        public ?string $periodEnd = null,
        public ?int $amountMinor = null,
        public ?string $currency = null,
        public ?string $adjustmentId = null,
    ) {
        self::reference($id); self::reference($subscriptionId); self::date($occurredAt);
        if (!in_array($type, ['paid','failed','renewal_cancelled','renewal_resumed','refund','chargeback'], true)) {
            throw new \InvalidArgumentException('invalid_billing_event');
        }
        if (in_array($type, ['paid','refund','chargeback'], true)) {
            self::reference($paymentId ?? '');
            if ($amountMinor === null || $amountMinor < 1 || $amountMinor > 100000000
                || !preg_match('/^[A-Z]{3}$/D', $currency ?? '')) throw new \InvalidArgumentException('invalid_billing_amount');
        }
        if ($type === 'paid') {
            self::date($periodStart ?? ''); self::date($periodEnd ?? '');
            if ($periodEnd <= $periodStart) throw new \InvalidArgumentException('invalid_billing_period');
        }
        if ($type === 'refund' || $type === 'chargeback') self::reference($adjustmentId ?? '');
    }

    public static function reference(string $value): void
    {
        if (!preg_match('/^[A-Za-z0-9_.:-]{1,191}$/D', $value)) throw new \InvalidArgumentException('invalid_billing_reference');
    }

    public static function date(string $value): void
    {
        $date = \DateTimeImmutable::createFromFormat('!Y-m-d H:i:s.u', $value, new \DateTimeZone('UTC'));
        if (!$date || $date->format('Y-m-d H:i:s.u') !== $value) throw new \InvalidArgumentException('invalid_billing_date');
    }
}
