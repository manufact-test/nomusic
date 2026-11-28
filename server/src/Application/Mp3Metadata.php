<?php

declare(strict_types=1);
namespace Celikom\Application;

/** Bounded standard tags outside an already validated MPEG frame interval. */
final class Mp3Metadata
{
    /** @return array{position:int,end:int,kinds:array,padding:int}|null */
    public static function tail(string $data, int $audioEnd): ?array
    {
        $size = strlen($data); $position = $audioEnd; $end = $size;
        $padding = 0; $metadataBytes = 0; $kinds = [];
        $marker = static fn(int $p, string $s): bool => $p >= $audioEnd && $p + strlen($s) <= $size && substr($data, $p, strlen($s)) === $s;
        $digits = static function (int $p, int $n) use ($data, $audioEnd, $size): ?int {
            if ($p < $audioEnd || $p + $n > $size) return null;
            $text = substr($data, $p, $n); return preg_match('/^[0-9]+$/D', $text) ? (int) $text : null;
        };
        $u32 = static fn(int $p): int => unpack('V', substr($data, $p, 4))[1];
        $consume = static function (int $next, string $kind) use (&$position, &$end, &$metadataBytes, &$kinds): bool {
            $metadataBytes += $end - $next;
            if ($next < $position || $metadataBytes > 8388608 || count($kinds) >= 16) return false;
            $end = $next; $kinds[] = $kind; return true;
        };
        while ($end > $position) {
            if ($end - $position >= 128 && $marker($end - 128, 'TAG')) { if (!$consume($end - 128, 'id3v1')) return null; continue; }
            if ($end - $position >= 227 && $marker($end - 227, 'TAG+')) { if (!$consume($end - 227, 'id3v1-enhanced')) return null; continue; }
            if ($end - $position >= 32 && $marker($end - 32, 'APETAGEX')) {
                $at = $end - 32; $v = $u32($at + 8); $bytes = $u32($at + 12); $items = $u32($at + 16);
                if (!in_array($v, [1000, 2000], true) || $bytes < 32 || $bytes > 1048576 || $items > 128 || $bytes > $end - $position) return null;
                $start = $end - $bytes;
                if ($start - $position >= 32 && $marker($start - 32, 'APETAGEX')) {
                    if ($v !== 2000 || $u32($start - 24) !== $v || $u32($start - 20) !== $bytes) return null;
                    $start -= 32;
                }
                if (!$consume($start, $v === 1000 ? 'apev1' : 'apev2')) return null; continue;
            }
            if ($end - $position >= 15 && $marker($end - 9, 'LYRICS200')) {
                $bytes = $digits($end - 15, 6); $start = $bytes === null ? -1 : $end - 15 - $bytes;
                if ($bytes === null || $bytes < 19 || $start < $position || !$marker($start, 'LYRICSBEGIN')) return null;
                $cursor = $start + 11; $fields = 0;
                while ($cursor < $end - 15) {
                    if ($cursor + 8 > $end - 15 || !preg_match('/^[A-Z]{3}$/D', substr($data, $cursor, 3))) return null;
                    $length = $digits($cursor + 3, 5);
                    if ($length === null || $cursor + 8 + $length > $end - 15 || ++$fields > 128) return null;
                    $cursor += 8 + $length;
                }
                if ($cursor !== $end - 15 || $fields === 0 || !$consume($start, 'lyrics3v2')) return null; continue;
            }
            if ($end - $position >= 20 && $marker($end - 9, 'LYRICSEND')) {
                $start = -1;
                for ($p = max($position, $end - 5120); $p <= $end - 20; ++$p) {
                    if ($marker($p, 'LYRICSBEGIN') && !preg_match('/[\x00-\x08\x0b\x0c\x0e-\x1f\xff]/', substr($data, $p + 11, $end - 9 - $p - 11))) { $start = $p; break; }
                }
                if ($start < 0) return null;
                if (!$consume($start, 'lyrics3v1')) return null; continue;
            }
            if ($marker($position, 'TAG') && $end - $position >= 128 && $end - $position <= 512) {
                $length = $end - $position;
                $valid = $length === 128 || trim(substr($data, $position + 128, $end - $position - 128), "\0") === '';
                if (!$valid) {
                    $text = substr($data, $position + 3, $length - 4);
                    $valid = preg_match('//u', $text) === 1 && preg_match_all('/./us', $text) === 124 && !preg_match('/[\x01-\x1f\x7f]/u', $text);
                }
                if ($valid) { if (!$consume($position, 'id3v1-legacy')) return null; continue; }
            }
            if ($marker($position, 'ID3') && $position + 10 <= $end) {
                $version = ord($data[$position + 3]); $flags = ord($data[$position + 5]);
                $reserved = $version === 2 ? 0x3f : ($version === 3 ? 0x1f : 0x0f);
                if (!in_array($version, [2, 3, 4], true) || ord($data[$position + 4]) === 255 || ($flags & $reserved)) return null;
                $length = 0;
                for ($i = 6; $i < 10; ++$i) { $c = ord($data[$position + $i]); if ($c & 128) return null; $length = ($length << 7) | $c; }
                $length += 10 + ($version === 4 && ($flags & 16) ? 10 : 0);
                if ($position + $length > $end || $length > 8388608 || ($version === 4 && ($flags & 16) && !$marker($position + $length - 10, '3DI'))) return null;
                $metadataBytes += $length; if ($metadataBytes > 8388608 || count($kinds) >= 16) return null;
                $position += $length; $kinds[] = 'id3v2-tail'; continue;
            }
            if ($data[$end - 1] === "\0") { if (++$padding > 4096) return null; --$end; continue; }
            break;
        }
        return ['position' => $position, 'end' => $end, 'kinds' => $kinds, 'padding' => $padding];
    }

    public static function orphanXmp(string $tail): bool
    {
        if (strlen($tail) > 4096) return false;
        $text = ltrim($tail, "\0"); $zeros = strlen($tail) - strlen($text);
        if ($zeros < 32 || $text === '' || preg_match('/[^\x09\x0a\x0d\x20-\x7e]/', $text)) return false;
        $text = preg_replace('/[ \t\r\n]+/', ' ', trim($text));
        foreach (['<?xpacket end="r"?>', '<?xpacket end="w"?>'] as $closing) if (str_ends_with($text, $closing)) $text = trim(substr($text, 0, -strlen($closing)));
        if (!preg_match('~</rdf:Description> ?</rdf:RDF> ?</x:xmpmeta>$~D', $text, $match, PREG_OFFSET_CAPTURE)) return false;
        $head = trim(substr($text, 0, $match[0][1]));
        if (!preg_match('~/?>$~D', $head)) return false;
        $properties = explode(' ', trim(preg_replace('~/?>$~D', '', $head)));
        if (count($properties) > 4) return false;
        $id = '(?:xmp\.did:)?[A-Fa-f0-9-]{8,64}';
        $property = '~^stRef:(?:instanceID|documentID|originalDocumentID)="' . $id . '"$~D';
        $first = preg_match($property, $properties[0]) || preg_match('~^' . $id . '"$~D', $properties[0]);
        $seen = false;
        foreach ($properties as $i => $value) { $valid = preg_match($property, $value); $seen = $seen || (bool) $valid; if ($i > 0 && !$valid) return false; }
        return (bool) $first && $seen;
    }
}
