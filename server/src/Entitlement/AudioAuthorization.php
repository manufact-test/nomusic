<?php
declare(strict_types=1);
namespace Celikom\Entitlement;

/** Production AudioAccessService authorizes every HEAD and Range request. */
interface AudioAuthorization
{
    public function allowed(int $sessionId): bool;
}
