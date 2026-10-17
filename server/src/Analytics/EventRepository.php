<?php

declare(strict_types=1);

namespace Celikom\Analytics;

interface EventRepository
{
    public function insert(array $event): bool;
}
