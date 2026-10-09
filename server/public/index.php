<?php

declare(strict_types=1);

ini_set('display_errors', '0');
ini_set('zlib.output_compression', '0');
require dirname(__DIR__) . '/bootstrap.php';

$config = require dirname(__DIR__) . '/config/app.php';
$app = new Celikom\Application($config);
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$headers = function_exists('getallheaders') ? getallheaders() : [];
$multipart = $method === 'POST' && str_starts_with(strtolower($_SERVER['CONTENT_TYPE'] ?? ''), 'multipart/form-data');
$body = $method === 'POST' && !$multipart ? file_get_contents('php://input', false, null, 0, 65537) : '';

$response = $app->handle($method, $path, $_GET, $headers, $body === false ? '' : $body, $multipart ? $_POST : [], $multipart ? $_FILES : []);

while (ob_get_level() > 0) {
    ob_end_clean();
}
http_response_code($response->status);
foreach ($response->headers as $name => $value) {
    header($name . ': ' . $value);
}
if ($method !== 'HEAD') {
    $response->emitBody();
}
