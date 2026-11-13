<?php

declare(strict_types=1);

namespace Celikom\Http;

final class ByteRange
{
    /** Single byte range only; unsupported/malformed ranges return 416. @return array{int, int} */
    public static function parse(string $header, int $size): array
    {
        if ($size <= 0 || !preg_match('/^bytes=(\d{0,18})-(\d{0,18})$/D', trim($header), $match) || ($match[1] === '' && $match[2] === '')) {
            throw new \InvalidArgumentException('range_not_satisfiable');
        }
        if ($match[1] === '') {
            $suffix = (int) $match[2];
            if ($suffix <= 0) {
                throw new \InvalidArgumentException('range_not_satisfiable');
            }
            return [max(0, $size - $suffix), $size - 1];
        }
        $start = (int) $match[1];
        $end = $match[2] === '' ? $size - 1 : min((int) $match[2], $size - 1);
        if ($start >= $size || $start > $end) {
            throw new \InvalidArgumentException('range_not_satisfiable');
        }
        return [$start, $end];
    }
}
