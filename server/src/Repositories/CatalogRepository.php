<?php

declare(strict_types=1);

namespace Celikom\Repositories;

interface CatalogRepository
{
    /** Return only the currently active approved mapping, or null. */
    public function findActive(string $service, string $trackId): ?array;
    public function findByReplacement(int $id): ?array;
}
