<?php

declare(strict_types=1);

namespace Celikom\Application;

use Celikom\Storage\StorageAdapter;

/**
 * Optional, immutable, pre-rendered Windows-only audio. Never transcode in PHP.
 * Stale, missing or mismatched sidecars cannot replace the approved original.
 */
final class WindowsGainVariant
{
    public const PROFILE = 'windows_gain_v1';

    public static function select(array $row, StorageAdapter $storage): ?array
    {
        $gain = (float) ($row['gain_db'] ?? 0);
        if (!is_finite($gain) || $gain === 0.0 || $gain < -12 || $gain > 12
            || abs($gain * 10 - round($gain * 10)) > 0.00001
            || ($row['storage_driver'] ?? '') !== 'local'
            || ($row['windows_variant_mime_type'] ?? '') !== 'audio/mpeg'
            || ($row['mime_type'] ?? '') !== 'audio/mpeg'
            || !is_string($row['sha256'] ?? null)
            || preg_match('/^[a-f0-9]{64}$/D', $row['sha256']) !== 1
            || ($row['windows_variant_source_sha256'] ?? '') !== $row['sha256']
            || (int)($row['windows_variant_source_version'] ?? 0) !== (int)($row['version'] ?? -1)
            || !is_numeric($row['windows_variant_gain_db'] ?? null)
            || abs((float)$row['windows_variant_gain_db'] - $gain) > 0.00001)
            return null;

        $key = $row['windows_variant_storage_key'] ?? null;
        $sha = $row['windows_variant_sha256'] ?? null;
        $size = (int)($row['windows_variant_size_bytes'] ?? 0);
        $duration = (int)($row['windows_variant_duration_ms'] ?? 0);
        if (!is_string($key) || preg_match('~^windows-gain/[a-f0-9]{2}/[a-f0-9]{64}\.mp3$~D', $key) !== 1
            || !is_string($sha) || preg_match('/^[a-f0-9]{64}$/D', $sha) !== 1
            || !str_ends_with($key, '/'.$sha.'.mp3')
            || $size < 1024 || $size > 31457280
            || $duration <= 0 || abs($duration - (int)($row['duration_ms'] ?? 0)) > 1500)
            return null;

        try {
            if (!$storage->exists($key) || $storage->getSize($key) !== $size) return null;
        } catch (\Throwable) {
            return null;
        }

        return [
            'storage_key' => $key, 'sha256' => $sha, 'size_bytes' => $size,
            'mime_type' => 'audio/mpeg', 'duration_ms' => $duration,
        ];
    }
}
