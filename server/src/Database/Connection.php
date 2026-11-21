<?php

declare(strict_types=1);

namespace Celikom\Database;

final class Connection
{
    public static function open(array $config): \PDO
    {
        if (!($config['db_name'] ?? '') || !($config['db_user'] ?? '')) {
            throw new \RuntimeException('database_not_configured');
        }
        $dsn = sprintf('mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4', $config['db_host'], $config['db_port'], $config['db_name']);
        return new \PDO($dsn, $config['db_user'], $config['db_password'], [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_EMULATE_PREPARES => false,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
        ]);
    }
}
