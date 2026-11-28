<?php

declare(strict_types=1);

namespace Celikom\Application;

/* Lossless, bounded metadata cleanup. Coded audio is never skipped; only a proven missing ancillary slot may be restored. */
final class Mp3Normalizer
{
    /** @return array{path:string,duration_ms:int,size:int} Caller must unlink path. */
    public function prepare(string $path): array
    {
        $size = filesize($path);
        if ($size === false || $size < 1024 || $size > 31457280) throw new \DomainException('invalid_mp3');
        $data = file_get_contents($path);
        if ($data === false || strlen($data) !== $size) throw new \RuntimeException('upload_unreadable');
        $position = 0; $tags = 0; $metadataBytes = 0;
        $skipTags = static function () use ($data, $size, &$position, &$tags, &$metadataBytes): void {
            while (substr($data, $position, 3) === 'ID3') {
                if ($position + 10 > $size || ++$tags > 4) throw new \DomainException('invalid_mp3');
                $h = substr($data, $position, 10); $v = ord($h[3]); $flags = ord($h[5]);
                if (!in_array($v, [2,3,4], true) || ord($h[4]) === 255 ||
                    ($flags & ($v === 2 ? 0x3f : ($v === 3 ? 0x1f : 0x0f))) !== 0) throw new \DomainException('invalid_mp3');
                $length = 0;
                for ($i = 6; $i < 10; ++$i) {
                    if (ord($h[$i]) & 128) throw new \DomainException('invalid_mp3');
                    $length = ($length << 7) | ord($h[$i]);
                }
                $length += 10 + ($v === 4 && ($flags & 16) ? 10 : 0);
                $metadataBytes += $length;
                if ($position + $length > $size || $metadataBytes > 8388608 ||
                    ($v === 4 && ($flags & 16) && substr($data, $position + $length - 10, 3) !== '3DI')) throw new \DomainException('invalid_mp3');
                $position += $length;
            }
        };
        $skipTags();
        $firstInfo = ''; $headerCount = 0; $signature = null;
        while (($frame = self::frame($data, $position)) !== null && $frame['metadata']) {
            if (++$headerCount > 4 || ($signature !== null &&
                ($signature['rate'] !== $frame['rate'] || $signature['version'] !== $frame['version']))) throw new \DomainException('invalid_mp3');
            $signature = $frame;
            if ($firstInfo === '') $firstInfo = substr($data, $position, $frame['bytes']);
            $position += $frame['bytes']; $skipTags();
        }
        $start = $position; $frames = 0; $repairedAncillaryByte = false; $samples = 0; $rate = $signature['rate'] ?? 0; $version = $signature['version'] ?? null;
        while (($frame = self::frame($data, $position, $frames >= 2)) !== null) {
            if ($frame['metadata'] || ($rate && ($rate !== $frame['rate'] || $version !== $frame['version']))) throw new \DomainException('invalid_mp3');
            $rate = $frame['rate']; $version = $frame['version']; $samples += $frame['samples']; $position += $frame['bytes'];
            $repairedAncillaryByte = $repairedAncillaryByte || $frame['repair'];
            if (++$frames > 500000 || $samples / $rate > 86400) throw new \DomainException('invalid_mp3');
        }
        if ($frames < 2) throw new \DomainException('invalid_mp3');
        $audioEnd = $position;
        $tail = Mp3Metadata::tail($data, $audioEnd);
        if ($tail === null) throw new \DomainException('invalid_mp3');
        $position = $tail['position']; $end = $tail['end'];
        if (Mp3Metadata::orphanXmp(substr($data, $position, $end - $position))) $position = $end;
        if ($end < $position || $end - $position > 4096 || trim(substr($data, $position, $end - $position), "\0") !== '') throw new \DomainException('invalid_mp3');
        $output = tempnam(sys_get_temp_dir(), 'celikom-mp3-');
        if ($output === false) throw new \RuntimeException('upload_storage_failed');
        try {
            chmod($output, 0600);
            $clean = $firstInfo . substr($data, $start, $audioEnd - $start) . ($repairedAncillaryByte ? "\0" : '');
            if (file_put_contents($output, $clean) !== strlen($clean)) throw new \RuntimeException('upload_storage_failed');
            $duration = (new Mp3Inspector())->durationMs($output);
            if ($duration === null) throw new \DomainException('invalid_mp3');
            return ['path' => $output, 'duration_ms' => $duration, 'size' => strlen($clean)];
        } catch (\Throwable $e) { unlink($output); throw $e; }
    }

    private static function frame(string $data, int $p, bool $allowFinalRepair = false): ?array
    {
        if ($p + 4 > strlen($data)) return null;
        $h = unpack('N', substr($data, $p, 4))[1];
        $v = ($h >> 19) & 3; $index = ($h >> 12) & 15; $ri = ($h >> 10) & 3;
        if (($h & 0xffe00000) !== 0xffe00000 || $v === 1 || (($h >> 17) & 3) !== 1 || $index < 1 || $index > 14 || $ri === 3) return null;
        $rate = intdiv([44100,48000,32000][$ri], $v === 3 ? 1 : ($v === 2 ? 2 : 4));
        $bitrate = ($v === 3 ? [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320] : [0,8,16,24,32,40,48,56,64,80,96,112,128,144])[$index];
        $bytes = (int) floor(($v === 3 ? 144 : 72) * $bitrate * 1000 / $rate) + (($h >> 9) & 1);
        if ($bytes < 24 || $bytes > 1441) return null;
        $repair = $p + $bytes > strlen($data);
        if ($repair && (!$allowFinalRepair || !self::ancillaryByteMissing($data, $p, $h, $bytes))) return null;
        $crc = ($h >> 16) & 1 ? 0 : 2; $mono = (($h >> 6) & 3) === 3;
        $side = $v === 3 ? ($mono ? 17 : 32) : ($mono ? 9 : 17);
        $info = $p + 4 + $crc + $side;
        $metadata = $info + 8 <= $p + $bytes && in_array(substr($data, $info, 4), ['Info','Xing'], true) && trim(substr($data, $p + 4 + $crc, $side), "\0") === '';
        return ['bytes' => $repair ? $bytes - 1 : $bytes, 'repair' => $repair, 'rate' => $rate, 'version' => $v, 'samples' => $v === 3 ? 1152 : 576, 'metadata' => $metadata];
    }

    private static function ancillaryByteMissing(string $data, int $p, int $h, int $bytes): bool
    {
        $size = strlen($data);
        if ($p + $bytes !== $size + 1 || (($h >> 19) & 3) !== 3 || !(($h >> 16) & 1) || !(($h >> 9) & 1)) return false;
        $channels = (($h >> 6) & 3) === 3 ? 1 : 2; $side = $channels === 1 ? 17 : 32;
        if ($p + 4 + $side > $size) return false;
        $bit = 0;
        $read = static function (int $n) use ($data, $p, &$bit): int {
            $value = 0;
            for ($i = 0; $i < $n; ++$i, ++$bit) $value = ($value << 1) | ((ord($data[$p + 4 + ($bit >> 3)]) >> (7 - ($bit & 7))) & 1);
            return $value;
        };
        $back = $read(9); $bit += ($channels === 1 ? 5 : 3) + $channels * 4;
        $codedBits = 0;
        for ($i = 0; $i < $channels * 2; ++$i) { $codedBits += $read(12); $bit += 47; }
        return $codedBits > 0 && $codedBits <= ($back + $size - $p - 4 - $side) * 8;
    }
}
