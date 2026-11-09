<?php

declare(strict_types=1);

// W30: patch only a copied immutable CELIKOM release, NEVER current.
// No credentials, database, account data or private audio are read.
if ($argc !== 2 || !is_file($argv[1]) || is_link($argv[1]) ||
    !str_contains((string) realpath($argv[1]), '/releases/w30-audio-cors-')) {
    fwrite(STDERR, "W30_INVALID_CANDIDATE\n");
    exit(2);
}
$path = $argv[1];
$source = file_get_contents($path);
if (!is_string($source) || str_contains($source, 'isNativeAudioOrigin')) {
    fwrite(STDERR, "W30_UNSUPPORTED_OR_ALREADY_PATCHED\n");
    exit(2);
}
$steps = [
    [
        <<<'SOURCE'
        if (in_array($headers['origin'] ?? '', $this->config['allowed_origins'], true)) {
SOURCE,
        <<<'SOURCE'
        if (in_array($headers['origin'] ?? '', $this->config['allowed_origins'], true)
            || self::isNativeAudioOrigin($method, $path, $headers['origin'] ?? '')) {
SOURCE,
    ],
    [
        <<<'SOURCE'
    private function route(string $method, string $path, array $query, array $headers, string $body, array $fields, array $files): Response
    {
SOURCE,
        <<<'SOURCE'
    private static function isNativeAudioOrigin(string $method, string $path, string $origin): bool
    {
        // Opaque origin ONLY for token-scoped audio; HMAC/session/Range remain.
        return in_array($method, ['GET', 'HEAD', 'OPTIONS'], true)
            && preg_match('~^/api/v1/audio/[1-9]\d{0,17}$~D', $path) === 1
            && in_array($origin, [
                'null',
                'musicapplication://desktop',
                'https://desktop.app.music.yandex.net',
                'https://next.music.yandex.ru',
                'https://music.yandex.com',
            ], true);
    }

    private function route(string $method, string $path, array $query, array $headers, string $body, array $fields, array $files): Response
    {
SOURCE,
    ],
    [
        <<<'SOURCE'
        if ($method === 'OPTIONS' && str_starts_with($path, '/api/v1/') && in_array($headers['origin'] ?? '', $this->config['allowed_origins'], true)) {
SOURCE,
        <<<'SOURCE'
        if ($method === 'OPTIONS' && str_starts_with($path, '/api/v1/') &&
            (in_array($headers['origin'] ?? '', $this->config['allowed_origins'], true)
            || self::isNativeAudioOrigin($method, $path, $headers['origin'] ?? ''))) {
SOURCE,
    ],
];
foreach ($steps as $index => [$needle, $replacement]) {
    if (substr_count($source, $needle) !== 1) {
        fwrite(STDERR, "W30_VERSION_GUARD_FAILED_STEP_" . ($index + 1) . "\n");
        exit(3);
    }
    $source = str_replace($needle, $replacement, $source);
}
$permissions = fileperms($path) & 0777;
$temp = tempnam(dirname($path), '.w30-');
if ($temp === false) exit(4);
try {
    if (file_put_contents($temp, $source, LOCK_EX) !== strlen($source) ||
        !chmod($temp, $permissions) || !rename($temp, $path)) exit(4);
} finally { if (is_file($temp)) unlink($temp); }
echo "W30_NATIVE_AUDIO_CORS_APPLIED_TO_ISOLATED_RELEASE\n";
