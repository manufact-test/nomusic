<?php

declare(strict_types=1);

namespace Celikom\Storage;

final class LocalStorageAdapter implements StorageAdapter
{
    private readonly string $root;

    public function __construct(string $root)
    {
        if (!is_dir($root) && !mkdir($root, 0700, true) && !is_dir($root)) {
            throw new \RuntimeException('storage_unavailable');
        }
        $resolved = realpath($root);
        if ($resolved === false) {
            throw new \RuntimeException('storage_unavailable');
        }
        foreach ([dirname(__DIR__, 2) . '/public', $_SERVER['DOCUMENT_ROOT'] ?? ''] as $webRoot) {
            $public = $webRoot !== '' ? realpath($webRoot) : false;
            if ($public !== false && ($resolved === $public || str_starts_with($resolved, rtrim($public, '/') . '/'))) {
                throw new \RuntimeException('storage_must_be_private');
            }
        }
        $this->root = rtrim($resolved, DIRECTORY_SEPARATOR);
    }

    private function path(string $key, bool $createParents = false): string
    {
        if (!preg_match('/^[a-zA-Z0-9][a-zA-Z0-9._\/-]{0,240}$/D', $key)) {
            throw new \InvalidArgumentException('invalid_storage_key');
        }
        $parts = explode('/', $key);
        $path = $this->root;
        foreach ($parts as $index => $part) {
            if ($part === '' || $part === '.' || $part === '..') {
                throw new \InvalidArgumentException('invalid_storage_key');
            }
            $path .= '/' . $part;
            if (is_link($path)) {
                throw new \InvalidArgumentException('invalid_storage_key');
            }
            if ($createParents && $index < count($parts) - 1 && !is_dir($path) && !mkdir($path, 0700) && !is_dir($path)) {
                throw new \RuntimeException('storage_unavailable');
            }
        }
        return $path;
    }

    public function put(string $key, mixed $source): void
    {
        if (!is_resource($source)) {
            throw new \InvalidArgumentException('invalid_storage_source');
        }
        $path = $this->path($key, true);
        $temporary = dirname($path) . '/.tmp-' . bin2hex(random_bytes(12));
        $target = fopen($temporary, 'xb');
        if ($target === false) {
            throw new \RuntimeException('storage_unavailable');
        }
        try {
            chmod($temporary, 0600);
            if (stream_copy_to_stream($source, $target) === false || !fflush($target)) {
                throw new \RuntimeException('storage_write_failed');
            }
            fclose($target);
            $target = null;
            if (!rename($temporary, $path)) {
                throw new \RuntimeException('storage_write_failed');
            }
        } finally {
            if (is_resource($target)) {
                fclose($target);
            }
            if (is_file($temporary)) {
                unlink($temporary);
            }
        }
    }

    public function openStream(string $key): mixed
    {
        $stream = @fopen($this->path($key), 'rb');
        if ($stream === false) {
            throw new \RuntimeException('storage_object_missing');
        }
        return $stream;
    }

    public function exists(string $key): bool
    {
        return is_file($this->path($key));
    }

    public function delete(string $key): void
    {
        $path = $this->path($key);
        if (is_file($path) && !unlink($path)) {
            throw new \RuntimeException('storage_delete_failed');
        }
    }

    public function move(string $from, string $to): void
    {
        if (!rename($this->path($from), $this->path($to, true))) {
            throw new \RuntimeException('storage_move_failed');
        }
    }

    public function getSize(string $key): int
    {
        $size = @filesize($this->path($key));
        if ($size === false) {
            throw new \RuntimeException('storage_object_missing');
        }
        return $size;
    }

    public function getMimeType(string $key): string
    {
        return (new \finfo(FILEINFO_MIME_TYPE))->file($this->path($key)) ?: 'application/octet-stream';
    }
}
