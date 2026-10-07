<?php

declare(strict_types=1);

$root = dirname(__DIR__);
$composerAutoload = $root . '/vendor/autoload.php';

if (is_file($composerAutoload)) {
    require $composerAutoload;
} else {
    require $root . '/src/Application.php';
}

$config = require $root . '/config/app.php';
$app = new Celikom\Application($config);

$health = $app->handle('GET', '/health');
if ($health['status'] !== 200) {
    throw new RuntimeException('Health endpoint must return HTTP 200.');
}

$payload = json_decode($health['body'], true, 512, JSON_THROW_ON_ERROR);
if (($payload['status'] ?? null) !== 'ok' || ($payload['service'] ?? null) !== 'celikom-api') {
    throw new RuntimeException('Health endpoint returned an invalid payload.');
}

$missing = $app->handle('GET', '/missing');
if ($missing['status'] !== 404) {
    throw new RuntimeException('Unknown routes must fail closed with HTTP 404.');
}

fwrite(STDOUT, "CELIKOM server smoke test passed.\n");
