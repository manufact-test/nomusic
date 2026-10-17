<?php

declare(strict_types=1);
namespace Celikom\Support;

/** User dates are Moscow time; immutable timestamps remain UTC. */
final class MoscowTime
{
    public static function zone(): \DateTimeZone { return new \DateTimeZone('Europe/Moscow'); }
    public static function display(?string $utc): string
    {
        if ($utc===null || $utc==='') return '';
        return (new \DateTimeImmutable($utc,new \DateTimeZone('UTC')))->setTimezone(self::zone())->format('d.m.Y H:i');
    }
    public static function today(string $format='Y-m-d',int $offsetDays=0): string
    {
        return (new \DateTimeImmutable('now',self::zone()))->modify($offsetDays.' days')->format($format);
    }
    public static function utc(\DateTimeImmutable $date): string
    {
        return $date->setTimezone(new \DateTimeZone('UTC'))->format('Y-m-d H:i:s');
    }
}
