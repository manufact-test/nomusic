<?php

declare(strict_types=1);

namespace Celikom\Application;

/* Decode to a null sink. No transcoding, network access, shell, or media output. */
final class Mp3DecodeValidator
{
    public function check(string $path): void
    {
        $tools = dirname(__DIR__, 2) . '/tools';
        $binary = $tools . '/mp3-validator';
        if (!is_executable($binary) || !is_callable('proc_open')) throw new \RuntimeException('audio_validation_unavailable');
        // A short, bounded admission wait absorbs ordinary upload bursts without
        // adding decoder slots, blocking indefinitely, or holding database locks.
        $lock = null;
        $admissionDeadline = hrtime(true) + 2_000_000_000;
        do {
            $contended = false;
            for ($i = 0; $i < 2; ++$i) {
                $candidate = @fopen($tools . '/decode-slot-' . $i . '.lock', 'c');
                if ($candidate === false) continue;
                $wouldBlock = 0;
                if (flock($candidate, LOCK_EX | LOCK_NB, $wouldBlock)) { $lock = $candidate; break; }
                $contended = $contended || $wouldBlock === 1;
                fclose($candidate);
            }
            if ($lock !== null) break;
            $remainingNs = $admissionDeadline - hrtime(true);
            if (!$contended || $remainingNs <= 0) break;
            usleep((int) min(25_000, max(1, intdiv($remainingNs, 1000))));
        } while (hrtime(true) < $admissionDeadline);
        if ($lock === null) throw new \RuntimeException('audio_validation_busy');
        $process = null; $pipes = [];
        try {
            $process = proc_open([$binary, '-nostdin', '-hide_banner', '-v', 'error', '-xerror',
                '-err_detect', 'explode', '-threads', '1', '-protocol_whitelist', 'file',
                '-f', 'mp3', '-i', $path, '-map', '0:a:0', '-threads', '1', '-f', 'null', '-'],
                [0 => ['file', '/dev/null', 'r'], 1 => ['file', '/dev/null', 'w'], 2 => ['pipe', 'w']], $pipes,
                null, ['LANG' => 'C', 'LC_ALL' => 'C'], ['bypass_shell' => true]);
            if (!is_resource($process)) throw new \RuntimeException('audio_validation_unavailable');
            stream_set_blocking($pipes[2], false);
            $deadline = microtime(true) + 15; $errors = ''; $exit = -1;
            do {
                $chunk = stream_get_contents($pipes[2]);
                if ($chunk !== false) $errors .= $chunk;
                if (strlen($errors) > 8192) { proc_terminate($process, 9); throw new \DomainException('invalid_mp3'); }
                $status = proc_get_status($process);
                if (!$status['running']) { $exit = $status['exitcode']; break; }
                if (microtime(true) >= $deadline) { proc_terminate($process, 9); throw new \RuntimeException('audio_validation_timeout'); }
                usleep(10000);
            } while (true);
            $chunk = stream_get_contents($pipes[2]);
            if ($chunk !== false) $errors .= $chunk;
            if ($exit !== 0 || $errors !== '') throw new \DomainException('invalid_mp3');
        } finally {
            foreach ($pipes as $pipe) if (is_resource($pipe)) fclose($pipe);
            if (is_resource($process)) { $status = proc_get_status($process); if ($status['running']) proc_terminate($process, 9); proc_close($process); }
            flock($lock, LOCK_UN); fclose($lock);
        }
    }
}
