<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

final readonly class EntitlementResult
{
    public function __construct(
        public bool $allowed,
        public string $source,
        public ?string $validUntil,
        public string $reason,
    ) {}

    public function json(): array
    {
        return [
            'allowed' => $this->allowed,
            'source' => $this->source,
            'valid_until' => $this->validUntil,
            'reason' => $this->reason,
        ];
    }
}
