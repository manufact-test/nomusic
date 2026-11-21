<?php

declare(strict_types=1);

// Owner-only SSH/terminal bootstrap. Never pass password on command line or write it to logs.
require dirname(__DIR__) . '/bootstrap.php';

if (PHP_SAPI !== 'cli' || count($argv) !== 2
    || !preg_match('/^[a-zA-Z0-9_.-]{3,120}$/D', $argv[1])) {
    fwrite(STDERR, "Usage: php server/bin/admin-create.php <login>\nPassword is read from STDIN, not argv.\n");
    exit(2);
}
$password = rtrim((string) fgets(STDIN), "\r\n");
if (strlen($password) < 16 || strlen($password) > 256) {
    fwrite(STDERR, "Password must have 16–256 characters.\n");
    exit(2);
}
$config = require dirname(__DIR__) . '/config/app.php';
$pdo = Celikom\Database\Connection::open($config);
$hash = password_hash($password, PASSWORD_DEFAULT);
unset($password);
$insert = $pdo->prepare("INSERT INTO admins (login,password_hash,role,enabled)
    VALUES (?,?,'owner',1)");
try {
    $insert->execute([$argv[1],$hash]);
    fwrite(STDOUT, "Owner admin account created.\n");
} catch (PDOException $e) {
    // Never print the raw SQL error, connection string, or credentials.
    fwrite(STDERR, "Admin create failed (account may already exist).\n");
    exit(1);
}
