<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
$config = require dirname(__DIR__) . '/config/app.php';
if (PHP_SAPI !== 'cli' || !str_starts_with($config['db_name'], 'celikom_test')
    || preg_match('/^[a-f0-9]{64}$/D', $argv[1] ?? '') !== 1) exit(10);
try {
    $pdo = Celikom\Database\Connection::open($config);
    fwrite(STDOUT, "ready\n"); fflush(STDOUT);
    if (trim((string) fgets(STDIN)) !== 'go') exit(10);
    $limiter = new Celikom\Application\UploadRateLimiter($pdo);
    $allowed = 0;
    for ($i = 0; $i < 8; $i++) {
        if ($limiter->check($argv[1], 'track_request', 3)) $allowed++;
    }
    fwrite(STDOUT, json_encode(['allowed' => $allowed], JSON_THROW_ON_ERROR));
} catch (Throwable) { exit(9); }
