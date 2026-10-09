<?php

declare(strict_types=1);

namespace Celikom\Application;

/**
 * Conservative, bounded MPEG Layer III frame inspection.
 * No transcoding or untrusted media decoder runs in a web request.
 * Exact playback compatibility and rights are deferred to owner moderation.
 */
final class Mp3Inspector
{
    /** Returns independently measured MP3 frame duration (ms), or null on malformed data. */
    public function durationMs(string $path): ?int
    {
        $stream = @fopen($path, 'rb');
        if ($stream === false) {
            return null;
        }
        try {
            $size = @filesize($path);
            if ($size === false || $size < 1024) {
                return null;
            }
            $head = fread($stream, 10);
            if ($head === false || strlen($head) < 10) {
                return null;
            }
            $offset = 0;
            if (substr($head, 0, 3) === 'ID3') {
                $version = ord($head[3]);
                $flags = ord($head[5]);
                if (!in_array($version, [2, 3, 4], true) || ord($head[4]) === 255 ||
                    ($flags & ($version === 2 ? 0x3f : ($version === 3 ? 0x1f : 0x0f))) !== 0) {
                    return null;
                }
                for ($i = 6; $i < 10; ++$i) {
                    if ((ord($head[$i]) & 0x80) !== 0) {
                        return null;
                    }
                }
                $tagSize = (ord($head[6]) << 21) | (ord($head[7]) << 14)
                    | (ord($head[8]) << 7) | ord($head[9]);
                $offset = 10 + $tagSize + ($version === 4 && ($flags & 0x10) ? 10 : 0);
            }
            if ($offset < 0 || $offset >= $size - 1024) {
                return null;
            }
            $position = $offset;
            $frames = 0;
            $samples = 0;
            $sampleRate = null;
            $mpegVersion = null;
            while ($position + 4 <= $size) {
                if (fseek($stream, $position) !== 0) {
                    return null;
                }
                $header = fread($stream, 4);
                if ($header === false || strlen($header) !== 4) {
                    return null;
                }
                $frame = self::parseHeader($header);
                if ($frame === null) {
                    break;
                }
                if ($sampleRate !== null && ($sampleRate !== $frame['rate'] || $mpegVersion !== $frame['version'])) {
                    return null;
                }
                $sampleRate = $frame['rate'];
                $mpegVersion = $frame['version'];
                if ($position + $frame['bytes'] > $size) {
                    return null;
                }
                $position += $frame['bytes'];
                $frames++;
                $samples += $frame['samples'];
                if ($frames > 500000 || $samples / $sampleRate > 86400) {
                    return null;
                }
            }
            // Allow only an ID3v1 trailer and small all-zero encoder padding.
            $tail = $size - $position;
            if ($tail >= 128 && fseek($stream, $position) === 0 && fread($stream, 3) === 'TAG') {
                $position += 128;
                $tail -= 128;
            }
            if ($tail > 4096 || $frames < 2 || $sampleRate === null ||
                fseek($stream, $position) !== 0) {
                return null;
            }
            while ($tail > 0) {
                $chunk = fread($stream, min(4096, $tail));
                if ($chunk === false || strlen($chunk) === 0 || trim($chunk, "\x00") !== '') {
                    return null;
                }
                $tail -= strlen($chunk);
            }
            $ms = (int) round(1000 * $samples / $sampleRate);
            return $ms >= 1000 && $ms <= 86400000 ? $ms : null;
        } finally {
            fclose($stream);
        }
    }

    public function check(string $path): bool
    {
        return $this->durationMs($path) !== null;
    }

    /** @return array{bytes:int,samples:int,rate:int,version:int}|null */
    private static function parseHeader(string $bytes): ?array
    {
        if (strlen($bytes) !== 4) {
            return null;
        }
        $header = unpack('N', $bytes)[1];
        if (($header & 0xffe00000) !== 0xffe00000) {
            return null;
        }
        $version = ($header >> 19) & 3;
        $layer = ($header >> 17) & 3;
        $bitrateIndex = ($header >> 12) & 15;
        $rateIndex = ($header >> 10) & 3;
        if ($version === 1 || $layer !== 1 || $bitrateIndex < 1 || $bitrateIndex > 14 || $rateIndex === 3) {
            return null;
        }
        $bitrateKbps = ($version === 3
            ? [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
            : [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144])[$bitrateIndex];
        $rate = [44100, 48000, 32000][$rateIndex];
        if ($version === 2) $rate = intdiv($rate, 2);
        if ($version === 0) $rate = intdiv($rate, 4);
        $samples = $version === 3 ? 1152 : 576;
        $frameBytes = (int) floor(($version === 3 ? 144 : 72) * $bitrateKbps * 1000 / $rate)
            + (($header >> 9) & 1);
        if ($frameBytes < 24 || $frameBytes > 1441) {
            return null;
        }
        return ['bytes' => $frameBytes, 'samples' => $samples, 'rate' => $rate, 'version' => $version];
    }
}
