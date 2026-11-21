<?php

declare(strict_types=1);

namespace Celikom\Application;

/** Bounded ISO-BMFF inspection. Only local, unencrypted, single-track AAC-LC. */
final class M4aInspector
{
    private string $data = '';
    private int $nodes = 0;

    public function durationMs(string $path): ?int
    {
        $size = @filesize($path);
        if ($size === false || $size < 1024 || $size > 31457280) return null;
        $data = @file_get_contents($path);
        if ($data === false || strlen($data) !== $size) return null;
        $this->data = $data;
        $this->nodes = 0;
        try {
            return $this->inspect($size);
        } catch (\Throwable) {
            return null;
        } finally {
            $this->data = '';
        }
    }

    private function u32(int $p): int { return unpack('N', substr($this->data, $p, 4))[1]; }
    private function u16(int $p): int { return unpack('n', substr($this->data, $p, 2))[1]; }
    private function require(bool $ok): void { if (!$ok) throw new \DomainException('invalid_m4a'); }
    private function boxes(int $start, int $end): array
    {
        $out = [];
        for ($p = $start; $p < $end;) {
            $this->require(++$this->nodes <= 8192 && $end - $p >= 8);
            $n = $this->u32($p); $head = 8; $type = substr($this->data, $p + 4, 4);
            if ($n === 1) {
                $this->require($end - $p >= 16 && $this->u32($p + 8) === 0);
                $n = $this->u32($p + 12); $head = 16;
            }
            if ($n === 0) $n = $end - $p;
            $this->require($n >= $head && $n <= $end - $p);
            $out[] = ['type' => $type, 'start' => $p + $head, 'end' => $p + $n];
            $p += $n;
        }
        return $out;
    }
    private function one(array $boxes, string $type): array
    {
        $found = array_values(array_filter($boxes, static fn ($b) => $b['type'] === $type));
        $this->require(count($found) === 1); return $found[0];
    }
    private function children(array $box): array { return $this->boxes($box['start'], $box['end']); }
    private function length(array $b): int { return $b['end'] - $b['start']; }
    private function descriptor(int &$p, int $end, int $tag): int
    {
        $this->require($p < $end && ord($this->data[$p++]) === $tag);
        $n = 0;
        for ($i = 0; $i < 4; ++$i) {
            $this->require($p < $end); $b = ord($this->data[$p++]); $n = ($n << 7) | ($b & 127);
            if (($b & 128) === 0) { $this->require($n <= $end - $p); return $p + $n; }
        }
        throw new \DomainException('invalid_m4a');
    }
    private function inspect(int $size): int
    {
        $top = $this->boxes(0, $size);
        $this->require(($top[0]['type'] ?? '') === 'ftyp');
        foreach ($top as $b) $this->require($b['type'] !== 'moof');
        $mdat = $this->one($top, 'mdat'); $moov = $this->children($this->one($top, 'moov'));
        $this->require($this->length($mdat) >= 512);
        $mdia = $this->children($this->one($this->children($this->one($moov, 'trak')), 'mdia'));
        $hdlr = $this->one($mdia, 'hdlr'); $mdhd = $this->one($mdia, 'mdhd');
        $this->require($this->length($hdlr) >= 12 && substr($this->data, $hdlr['start'] + 8, 4) === 'soun');
        $p = $mdhd['start']; $this->require($this->length($mdhd) >= 24);
        $version = ord($this->data[$p]);
        if ($version === 0) { $rate = $this->u32($p + 12); $duration = $this->u32($p + 16); }
        else {
            $this->require($version === 1 && $this->length($mdhd) >= 36 && $this->u32($p + 24) === 0);
            $rate = $this->u32($p + 20); $duration = $this->u32($p + 28);
        }
        $this->require($rate > 0 && $duration >= $rate && $duration / $rate <= 86400);
        $minf = $this->children($this->one($mdia, 'minf'));
        $dref = $this->one($this->children($this->one($minf, 'dinf')), 'dref');
        $this->require($this->length($dref) >= 8 && $this->u32($dref['start'] + 4) === 1);
        $url = $this->one($this->boxes($dref['start'] + 8, $dref['end']), 'url ');
        $this->require($this->length($url) === 4 && $this->u32($url['start']) === 1);
        $tables = $this->children($this->one($minf, 'stbl'));
        $stsd = $this->one($tables, 'stsd'); $this->require($this->length($stsd) >= 8 && $this->u32($stsd['start'] + 4) === 1);
        $entry = $this->one($this->boxes($stsd['start'] + 8, $stsd['end']), 'mp4a'); $p = $entry['start'];
        $this->require($this->length($entry) >= 28 && $this->u16($p + 6) === 1 && $this->u16($p + 8) === 0);
        $channels = $this->u16($p + 16); $sampleRate = $this->u32($p + 24) >> 16;
        $this->require($channels >= 1 && $channels <= 2 && $sampleRate >= 8000 && $sampleRate <= 48000);
        $extras = $this->boxes($p + 28, $entry['end']);
        foreach ($extras as $b) $this->require(!in_array($b['type'], ['sinf', 'schm'], true));
        $esds = $this->one($extras, 'esds'); $this->require($this->length($esds) >= 8); $p = $esds['start'] + 4;
        $esEnd = $this->descriptor($p, $esds['end'], 3);
        $this->require($esEnd - $p >= 3 && ord($this->data[$p + 2]) === 0); $p += 3;
        $configEnd = $this->descriptor($p, $esEnd, 4);
        $this->require($configEnd - $p >= 13 && ord($this->data[$p]) === 0x40 && (ord($this->data[$p + 1]) >> 2) === 5); $p += 13;
        $ascEnd = $this->descriptor($p, $configEnd, 5);
        $this->require($ascEnd - $p >= 2); $asc = $this->u16($p);
        $freqIndex = ($asc >> 7) & 15; $configChannels = ($asc >> 3) & 15;
        $rates = [96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000, 7350];
        $this->require(($asc >> 11) === 2 && isset($rates[$freqIndex]) && $rates[$freqIndex] === $sampleRate && $configChannels >= 1 && $configChannels <= 2 && ($asc & 7) === 0);
        $stsz = $this->one($tables, 'stsz'); $p = $stsz['start']; $this->require($this->length($stsz) >= 12);
        $fixed = $this->u32($p + 4); $samples = $this->u32($p + 8);
        $this->require($samples > 0 && $samples <= 500000 && $this->length($stsz) === 12 + ($fixed ? 0 : 4 * $samples));
        $stts = $this->one($tables, 'stts'); $p = $stts['start']; $this->require($this->length($stts) >= 8);
        $entries = $this->u32($p + 4); $this->require($entries > 0 && $entries <= $samples && $this->length($stts) === 8 + 8 * $entries);
        $count = 0; $time = 0;
        for ($i = 0; $i < $entries; ++$i) {
            $n = $this->u32($p + 8 + 8 * $i); $delta = $this->u32($p + 12 + 8 * $i);
            $this->require($n > 0 && $delta > 0); $count += $n; $time += $n * $delta;
        }
        $this->require($count === $samples && abs($time - $duration) <= $rate / 10);
        $stsc = $this->one($tables, 'stsc'); $p = $stsc['start']; $this->require($this->length($stsc) >= 8);
        $entries = $this->u32($p + 4); $this->require($entries > 0 && $entries <= $samples && $this->length($stsc) === 8 + 12 * $entries);
        $runs = []; $previous = 0;
        for ($i = 0; $i < $entries; ++$i) {
            $first = $this->u32($p + 8 + 12 * $i); $n = $this->u32($p + 12 + 12 * $i);
            $this->require($first > $previous && ($i !== 0 || $first === 1) && $n > 0 && $n <= $samples && $this->u32($p + 16 + 12 * $i) === 1);
            $runs[] = [$first, $n]; $previous = $first;
        }
        $offsets = array_values(array_filter($tables, static fn ($b) => in_array($b['type'], ['stco', 'co64'], true)));
        $this->require(count($offsets) === 1); $offsets = $offsets[0]; $p = $offsets['start'];
        $this->require($this->length($offsets) >= 8); $chunks = $this->u32($p + 4); $width = $offsets['type'] === 'co64' ? 8 : 4;
        $this->require($chunks > 0 && $chunks <= $samples && $this->length($offsets) === 8 + $width * $chunks && $previous <= $chunks);
        $sample = 0; $run = 0; $lastEnd = $mdat['start'];
        for ($i = 0; $i < $chunks; ++$i) {
            while (isset($runs[$run + 1]) && $runs[$run + 1][0] <= $i + 1) ++$run;
            $q = $p + 8 + $i * $width;
            if ($width === 8) { $this->require($this->u32($q) === 0); $q += 4; }
            $offset = $this->u32($q); $bytes = 0; $n = $runs[$run][1];
            $this->require($sample + $n <= $samples);
            for ($j = 0; $j < $n; ++$j, ++$sample) {
                $length = $fixed ?: $this->u32($stsz['start'] + 12 + 4 * $sample);
                $this->require($length > 0); $bytes += $length;
            }
            $this->require($offset >= $lastEnd && $offset + $bytes <= $mdat['end']); $lastEnd = $offset + $bytes;
        }
        $this->require($sample === $samples);
        return (int) round($duration * 1000 / $rate);
    }
}
