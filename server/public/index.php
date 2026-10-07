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
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$response = $app->handle($method, $path);

http_response_code($response['status']);
foreach ($response['headers'] as $name => $value) {
    header($name . ': ' . $value);
}
echo $response['body'];
