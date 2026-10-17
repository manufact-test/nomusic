<?php
declare(strict_types=1);
namespace Celikom\Website;

use PDO;
use RuntimeException;

/** PDO connection factory. Configuration is server-side only, never exposed. */
final class Database
{
    public static function connect(array $settings): PDO
    {
        foreach (['host', 'dbname', 'user', 'password'] as $key) {
            if (!isset($settings[$key]) || !is_string($settings[$key])) {
                throw new RuntimeException('Missing database connection setting');
            }
        }
        $host = $settings['host'];
        $dbname = $settings['dbname'];
        if (!preg_match('/^[a-zA-Z0-9_.-]+$/D', $host) || !preg_match('/^[a-zA-Z0-9_-]+$/D', $dbname)) {
            throw new RuntimeException('Invalid database host or name');
        }
        $dsn = "mysql:host={$host};dbname={$dbname};charset=utf8mb4";
        return new PDO($dsn, $settings['user'], $settings['password'], [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
    }
}
