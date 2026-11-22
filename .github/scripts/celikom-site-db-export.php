<?php
declare(strict_types=1);
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli' || $argc !== 2 || $argv[1] !== 'precutover') exit(2);
try {
    $root = '/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com';
    $private = $root . '/celikom-private';
    $cfgPath = $private . '/staging-config.php';
    if (is_link($private) || is_link($cfgPath) || !is_file($cfgPath)
        || !is_file($private . '/app/staging-approved.php')
        || is_file($private . '/app/release-approved.php')) throw new RuntimeException('layout');
    $cfg = require $cfgPath;
    if (!is_array($cfg) || ($cfg['CELIKOM_SITE_DB_HOST'] ?? null) !== 'localhost'
        || !preg_match('/^u235811320_celikom_stage[a-zA-Z0-9_]*$/D', (string) ($cfg['CELIKOM_SITE_DB_NAME'] ?? '')))
        throw new RuntimeException('db-scope');
    $secrets = stream_get_contents(STDIN, 8192);
    if (!is_string($secrets) || substr_count($secrets, "\0") !== 1) throw new RuntimeException('credentials');
    [$user, $password] = explode("\0", $secrets, 2);
    if (!preg_match('/^u235811320_[a-zA-Z0-9_]+$/D', $user) || $password === '')
        throw new RuntimeException('credentials');
    $pdo = new PDO('mysql:host=localhost;dbname=' . $cfg['CELIKOM_SITE_DB_NAME'] . ';charset=utf8mb4', $user, $password, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);
    $tables = $pdo->query("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME")->fetchAll(PDO::FETCH_COLUMN);
    if (!is_array($tables) || count($tables) < 11 || count($tables) > 100
        || !in_array('content_revisions', $tables, true)
        || !in_array('media_assets', $tables, true)
        || !in_array('content_drafts', $tables, true)) throw new RuntimeException('tables');
    $pdo->exec('SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ');
    $pdo->beginTransaction();
    $q = static fn(string $x): string => '`' . str_replace('`', '``', $x) . '`';
    fwrite(STDOUT, "SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS=0;\n");
    foreach ($tables as $table) {
        if (!preg_match('/^[a-z][a-z0-9_]{0,63}$/D', $table)) throw new RuntimeException('name');
        $ddl = $pdo->query('SHOW CREATE TABLE ' . $q($table))->fetch(PDO::FETCH_NUM);
        if (!is_array($ddl) || !isset($ddl[1])) throw new RuntimeException('ddl');
        fwrite(STDOUT, $ddl[1] . ";\n");
    }
    foreach ($tables as $table) {
        $columns=[];
        foreach ($pdo->query('SHOW FULL COLUMNS FROM ' . $q($table)) as $f) {
            if (!str_contains(strtoupper((string)($f['Extra'] ?? '')), 'GENERATED')) $columns[] = $f['Field'];
        }
        if (!$columns) throw new RuntimeException('columns');
        $names = implode(', ', array_map($q, $columns));
        $stmt = $pdo->query('SELECT ' . $names . ' FROM ' . $q($table));
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $values=[];
            foreach (array_values($row) as $v) $values[] = $v === null ? 'NULL' : $pdo->quote((string)$v);
            fwrite(STDOUT, 'INSERT INTO ' . $q($table) . ' (' . $names . ') VALUES (' . implode(', ', $values) . ");\n");
        }
        $stmt->closeCursor();
    }
    fwrite(STDOUT, "SET FOREIGN_KEY_CHECKS=1;\n");
    $pdo->commit();
    fwrite(STDERR, 'SITE_SQL_EXPORT_PASS: ' . count($tables) . " tables, content retained privately\n");
} catch (Throwable $e) {
    fwrite(STDERR, "SITE_SQL_EXPORT_FAILED_SAFELY\n");
    exit(1);
}