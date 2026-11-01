<?php

declare(strict_types=1);

namespace Celikom\Storage;

interface StorageAdapter
{
    /** @param resource $source */
    public function put(string $key, mixed $source): void;
    /** @return resource */
    public function openStream(string $key): mixed;
    public function exists(string $key): bool;
    public function delete(string $key): void;
    public function move(string $from, string $to): void;
    public function getSize(string $key): int;
    public function getMimeType(string $key): string;
}
