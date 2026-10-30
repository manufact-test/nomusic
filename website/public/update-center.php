<?php
declare(strict_types=1);

/* CELIKOM Android-only download resolver. No CMS/auth/audio dependencies. */
$method = $_SERVER['REQUEST_METHOD'] ?? '';
if (!in_array($method, ['GET', 'HEAD'], true)) {
    header('Allow: GET, HEAD');
    http_response_code(405);
    exit;
}
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store, max-age=0');
header('X-Frame-Options: DENY');
$path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
$root = dirname(__DIR__, 2) . '/celikom-private/android-updates';
$pointer = $root . '/stable.json';
$fail = static function (int $code): never {
    http_response_code($code);
    header('Content-Type: text/plain; charset=utf-8');
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'HEAD') echo 'CELIKOM Android update unavailable';
    exit;
};
if (!in_array($path, ['/download/android', '/download/android/', '/updates/android/stable.json'], true)
    && !preg_match('~^/releases/android/([1-9][0-9]*)-([a-f0-9]{64})\\.apk$~D', (string)$path, $match)) {
    $fail(404);
}
if (!is_file($pointer) || is_link($pointer)) $fail(503);
$json = file_get_contents($pointer);
$data = is_string($json) ? json_decode($json, true) : null;
if (!is_array($data) || ($data['enabled'] ?? null) !== true
    || ($data['schemaVersion'] ?? null) !== 1
    || ($data['channel'] ?? null) !== 'stable'
    || ($data['packageName'] ?? null) !== 'pro.celikom.nativeprobe'
    || !is_int($data['versionCode'] ?? null) || $data['versionCode'] < 57
    || !preg_match('/^[a-f0-9]{64}$/D', (string)($data['apkSha256'] ?? ''))
    || !is_int($data['sizeBytes'] ?? null) || $data['sizeBytes'] < 100000
    || ($data['signerSha256'] ?? '') !== '67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f') {
    $fail(503);
}
$filename = $data['versionCode'] . '-' . $data['apkSha256'] . '.apk';
$apk = $root . '/releases/' . $filename;
if (!is_file($apk) || is_link($apk) || filesize($apk) !== $data['sizeBytes']) $fail(503);
if ($path === '/updates/android/stable.json') {
    header('Content-Type: application/json; charset=utf-8');
    header('Content-Length: ' . strlen($json));
    if ($method === 'GET') echo $json;
    exit;
}
if (!in_array($path, ['/download/android', '/download/android/'], true)
    && ($match[1] !== (string)$data['versionCode'] || $match[2] !== $data['apkSha256'])) {
    /* Immutable older releases may be served while updating; validate their on-disk digest. */
    $old = $root . '/releases/' . $match[1] . '-' . $match[2] . '.apk';
    if (!is_file($old) || is_link($old) || !hash_equals($match[2], hash_file('sha256', $old))) $fail(404);
    $apk = $old;
}
header('Content-Type: application/vnd.android.package-archive');
header('Content-Disposition: attachment; filename="CELIKOM-Android.apk"');
header('Content-Length: ' . filesize($apk));
header('Accept-Ranges: none');
if ($method === 'HEAD') exit;
$stream = fopen($apk, 'rb');
if ($stream === false) $fail(503);
fpassthru($stream);
fclose($stream);
