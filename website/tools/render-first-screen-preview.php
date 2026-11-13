<?php
declare(strict_types=1);

/**
 * Isolated Stage 4 first-screen developer preview; NEVER a public admin route.
 * No MySQL, no login bypass, no filesystem publication or network requests.
 */
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
if ($argc !== 2 || !is_file($argv[1]) || filesize($argv[1]) > 32768) {
    fwrite(STDERR, "Usage: php website/tools/render-first-screen-preview.php draft.json > preview.html\n");
    exit(2);
}

require dirname(__DIR__) . '/app/bootstrap.php';

try {
    $base = dirname(__DIR__);
    $raw = file_get_contents($argv[1]);
    if (!is_string($raw)) {
        throw new RuntimeException('Missing draft');
    }
    $draft = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($draft) || (array_is_list($draft) && $draft !== [])) {
        throw new InvalidArgumentException('Stage 4 draft must be a JSON object');
    }
    // This scoped preview intentionally accepts no FAQ/media/reward/SEO fields.
    // Future Stage 9 owner UI must authenticate editor, validate CSRF and
    // persist only verified fields before invoking the same content renderer.
    $template = file_get_contents($base . '/app/Templates/site-v10.html');
    $manifest = file_get_contents($base . '/app/Config/content-fields-v10.json');
    if (!is_string($template) || !is_string($manifest)) {
        throw new RuntimeException('Trusted website templates unavailable');
    }
    echo \Celikom\Website\FirstScreenDraft::render($template, $manifest, $draft);
} catch (\Throwable $exception) {
    fwrite(STDERR, "Stage 4 preview rejected invalid or unsafe content\n");
    exit(1);
}
