<?php
declare(strict_types=1);
namespace Celikom\Website;

use RuntimeException;

/**
 * Cooperative, process-level CMS write barrier for offline Stage 10.
 *
 * All website CMS writers MUST hold LOCK_SH for their whole operation
 * (including media write + DB commit). Coordinated backup holds LOCK_EX from
 * before its DB read view until the last validated manifest is on disk.
 *
 * Advisory flock only: direct SQL clients, uninstrumented workers and media
 * garbage collection bypass it. Never infer production readiness from this.
 */
final class CmsWriteQuiescence
{
    private mixed $handle;
    private bool $exclusive;
    private bool $held = true;

    private function __construct(mixed $handle, bool $exclusive)
    {
        $this->handle = $handle;
        $this->exclusive = $exclusive;
    }

    public static function writer(string $publicDirectory, int $timeoutMs = 150): self
    {
        return self::acquire($publicDirectory, false, $timeoutMs);
    }

    public static function snapshot(string $publicDirectory, int $timeoutMs = 2000): self
    {
        return self::acquire($publicDirectory, true, $timeoutMs);
    }

    private static function acquire(string $publicDirectory, bool $exclusive, int $timeoutMs): self
    {
        if ($timeoutMs < 0 || $timeoutMs > 5000) {
            throw new RuntimeException('Invalid CMS lock timeout');
        }
        $path = getenv('CELIKOM_SITE_WRITE_GATE_FILE');
        $public = realpath($publicDirectory);
        if (!is_string($path) || basename($path) !== '.celikom-cms-writes.lock' ||
            !is_string($public) || !is_dir($public) ||
            is_link($path) || is_link(dirname($path))) {
            throw new RuntimeException('Private CMS write gate is not configured');
        }
        $parent = realpath(dirname($path));
        if (!is_string($parent) || !is_dir($parent) || $parent === $public ||
            str_starts_with($parent, $public.'/') ||
            str_starts_with($public, $parent.'/') ||
            (fileperms($parent) & 0077) !== 0 ||
            $path !== $parent.'/.celikom-cms-writes.lock') {
            throw new RuntimeException('Write gate must be outside web root in a private directory');
        }
        if (file_exists($path) && (!is_file($path) || is_link($path) ||
            (fileperms($path) & 0077) !== 0)) {
            throw new RuntimeException('CMS write gate file is insecure');
        }
        $handle = @fopen($path, 'c+b');
        if ($handle === false) throw new RuntimeException('Cannot open the CMS write gate');
        try {
            if (!chmod($path, 0600) || is_link($path)) {
                throw new RuntimeException('CMS write gate permissions invalid');
            }
            $fileStat = fstat($handle);
            $pathStat = @stat($path);
            if (!is_array($fileStat) || !is_array($pathStat) ||
                $fileStat['dev'] !== $pathStat['dev'] ||
                $fileStat['ino'] !== $pathStat['ino'] ||
                ($fileStat['mode'] & 0170000) !== 0100000 ||
                ($fileStat['mode'] & 0077) !== 0 ||
                ($fileStat['nlink'] ?? 1) !== 1) {
                throw new RuntimeException('CMS gate must be a single private regular file');
            }
            $start = hrtime(true);
            $mode = ($exclusive ? LOCK_EX : LOCK_SH) | LOCK_NB;
            do {
                if (flock($handle, $mode)) {
                    return new self($handle, $exclusive);
                }
                if ((hrtime(true) - $start) / 1_000_000 >= $timeoutMs) break;
                usleep(20000);
            } while (true);
            throw new RuntimeException('CMS write gate is busy; safe retry required');
        } catch (\Throwable $e) {
            fclose($handle);
            throw $e;
        }
    }

    public function assertExclusive(): void
    {
        if (!$this->held || !$this->exclusive || !is_resource($this->handle)) {
            throw new RuntimeException('An active exclusive CMS freeze is mandatory');
        }
    }

    public function release(): void
    {
        if (!$this->held) return;
        $this->held = false;
        if (is_resource($this->handle)) {
            flock($this->handle, LOCK_UN);
            fclose($this->handle);
        }
    }

    public function __destruct()
    {
        $this->release();
    }
}
