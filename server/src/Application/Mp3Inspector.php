<?php

declare(strict_types=1);

namespace Celikom\Application;

/** Structural MP3 check only; moderation must still listen and verify duration/quality. */
final class Mp3Inspector
{
    public function check(string $path): bool
    {
        $file = @fopen($path, 'rb');
        if ($file === false) return false;
        try {
            $header = fread($file, 10);
            if ($header === false) return false;
            $offset = 0;
            if (substr($header, 0, 3) === 'ID3') {
                if (strlen($header) !== 10 || (ord($header[6]) | ord($header[7]) | ord($header[8]) | ord($header[9])) & 0x80) return false;
                $offset = 10 + ((ord($header[6]) << 21) | (ord($header[7]) << 14) | (ord($header[8]) << 7) | ord($header[9]));
                if ((ord($header[5]) & 0x10) !== 0) $offset += 10;
            }
            $size = @filesize($path);
            if ($size === false || $offset >= $size - 1024 || fseek($file, $offset) !== 0) return false;
            $bytes = fread($file, min(131072, $size - $offset));
            if ($bytes === false) return false;
            $length = strlen($bytes);
            for ($i = 0; $i + 8 < $length; $i++) {
                $frameSize = self::frameSize(substr($bytes, $i, 4));
                if ($frameSize !== null && $i + $frameSize + 4 <= $length
                    && self::frameSize(substr($bytes, $i + $frameSize, 4)) !== null) {
                    return true;
                }
            }
            return false;
        } finally {
            fclose($file);
        }
    }

    private static function frameSize(string $data): ?int
    {
        if (strlen($data) !== 4) return null;
        $h = unpack('N', $data)[1];
        if (($h & 0xffe00000) !== 0xffe00000) return null;
        $version = ($h >> 19) & 3;
        $layer = ($h >> 17) & 3;
        $bitrateIndex = ($h >> 12) & 15;
        $rateIndex = ($h >> 10) & 3;
        if ($version === 1 || $layer !== 1 || $bitrateIndex === 0 || $bitrateIndex === 15 || $rateIndex === 3) return null;
        $bitrate = ($version === 3
            ? [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320]
            : [0,8,16,24,32,40,48,56,64,80,96,112,128,144,160])[$bitrateIndex];
        $rate = [44100, 48000, 32000][$rateIndex] / ($version === 3 ? 1 : ($version === 2 ? 2 : 4));
        $padding = ($h >> 9) & 1;
        $size = (int) floor(($version === 3 ? 144 : 72) * $bitrate * 1000 / $rate) + $padding;
        return $size >= 24 && $size <= 1441 ? $size : null;
    }
}
