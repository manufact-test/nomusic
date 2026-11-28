<?php

declare(strict_types=1);

namespace Celikom\Application;

/** Canonical local AAC container, packet-copy only; independently inspect and decode. */
final class M4aNormalizer
{
    /** @return array{path:string,duration_ms:int,size:int} Caller must unlink path. */
    public function prepare(string $path): array
    {
        $size = filesize($path);
        if ($size === false || $size < 1024 || $size > 31457280 || is_link($path)) throw new \DomainException('invalid_m4a');
        $tools = dirname(__DIR__, 2) . '/tools';
        $binary = $tools . '/m4a-normalizer';
        if (!is_executable($binary) || !is_callable('proc_open')) throw new \RuntimeException('audio_validation_unavailable');
        // Share the existing two admission slots with MP3; no extra decoder pool.
        $lock = null; $deadline = hrtime(true) + 2_000_000_000;
        do {
            $contended = false;
            for ($i = 0; $i < 2; ++$i) {
                $candidate = @fopen($tools . '/decode-slot-' . $i . '.lock', 'c');
                if ($candidate === false) continue;
                $wouldBlock = 0;
                if (flock($candidate, LOCK_EX | LOCK_NB, $wouldBlock)) { $lock = $candidate; break; }
                $contended = $contended || $wouldBlock === 1; fclose($candidate);
            }
            if ($lock !== null) break;
            $remaining = $deadline - hrtime(true);
            if (!$contended || $remaining <= 0) break;
            usleep((int) min(25_000, max(1, intdiv($remaining, 1000))));
        } while (true);
        if ($lock === null) throw new \RuntimeException('audio_validation_busy');
        $output = null;
        try {
            $output = tempnam(sys_get_temp_dir(), 'celikom-m4a-');
            if ($output === false) throw new \RuntimeException('upload_storage_failed');
            chmod($output, 0600);
            $common = [$binary, '-nostdin', '-hide_banner', '-v', 'error', '-xerror', '-max_alloc', '67108864',
                '-err_detect', 'explode', '-threads', '1', '-protocol_whitelist', 'file',
                '-enable_drefs', '0', '-use_absolute_path', '0', '-f', 'mov'];
            self::run([...$common, '-i', $path, '-map', '0:a', '-c:a', 'copy',
                '-map_metadata', '-1', '-map_chapters', '-1', '-movflags', '+faststart',
                '-fs', '31457280', '-f', 'ipod', '-y', $output]);
            clearstatcache(true, $output); $bytes = filesize($output);
            if ($bytes === false || $bytes < 1024 || $bytes >= 31457280) throw new \DomainException('invalid_m4a');
            $duration = (new M4aInspector())->durationMs($output);
            if ($duration === null) throw new \DomainException('invalid_m4a');
            self::run([...$common, '-i', $output, '-map', '0:a:0', '-threads', '1', '-f', 'null', '-']);
            $result = ['path' => $output, 'duration_ms' => $duration, 'size' => $bytes];
            $output = null; return $result;
        } finally {
            if (is_string($output) && is_file($output)) unlink($output);
            flock($lock, LOCK_UN); fclose($lock);
        }
    }

    private static function run(array $args): void
    {
        $process = null; $pipes = [];
        try {
            $process = proc_open($args, [0 => ['file', '/dev/null', 'r'], 1 => ['file', '/dev/null', 'w'], 2 => ['pipe', 'w']],
                $pipes, null, ['LANG' => 'C', 'LC_ALL' => 'C'], ['bypass_shell' => true]);
            if (!is_resource($process)) throw new \RuntimeException('audio_validation_unavailable');
            stream_set_blocking($pipes[2], false);
            $deadline = microtime(true) + 15; $errors = ''; $exit = -1;
            do {
                $chunk = stream_get_contents($pipes[2]); if ($chunk !== false) $errors .= $chunk;
                if (strlen($errors) > 8192) { proc_terminate($process, 9); throw new \DomainException('invalid_m4a'); }
                $status = proc_get_status($process);
                if (!$status['running']) { $exit = $status['exitcode']; break; }
                if (microtime(true) >= $deadline) { proc_terminate($process, 9); throw new \RuntimeException('audio_validation_timeout'); }
                usleep(10000);
            } while (true);
            $chunk = stream_get_contents($pipes[2]); if ($chunk !== false) $errors .= $chunk;
            if ($exit !== 0 || $errors !== '') throw new \DomainException('invalid_m4a');
        } finally {
            foreach ($pipes as $pipe) if (is_resource($pipe)) fclose($pipe);
            if (is_resource($process)) { $status = proc_get_status($process); if ($status['running']) proc_terminate($process, 9); proc_close($process); }
        }
    }
}
