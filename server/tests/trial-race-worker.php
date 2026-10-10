<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
$config = require dirname(__DIR__) . '/config/app.php';
if (PHP_SAPI !== 'cli' || !str_starts_with($config['db_name'], 'celikom_test')
    || !ctype_digit($argv[1] ?? '')) exit(10);
try {
    $pdo = Celikom\Database\Connection::open($config);
    fwrite(STDOUT, "ready\n");
    fflush(STDOUT);
    $result = (new Celikom\Entitlement\TrialService($pdo))->activate((int)$argv[1]);
    fwrite(STDOUT, json_encode($result, JSON_THROW_ON_ERROR) . "\n");
} catch (Throwable) { exit(9); }
