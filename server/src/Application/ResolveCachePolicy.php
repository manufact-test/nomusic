<?php

declare(strict_types=1);

namespace Celikom\Application;

/** Shared and bounded TTL values in seconds. Audio token validity is separate. */
final class ResolveCachePolicy
{
    public static function positive(int $requested, int $audioTokenTtl): int
    {
        return max(5, min(120, $requested, $audioTokenTtl - 30));
    }

    public static function negative(int $requested): int
    {
        return max(5, min(60, $requested));
    }
}
