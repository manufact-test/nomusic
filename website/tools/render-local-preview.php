<?php
declare(strict_types=1);

// Stage 3 developer-only CLI preview. NOT an /admin endpoint, API or public
// route. Never use this to publish a site without the full secure CMS.
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
if ($argc !== 2 || !is_file($argv[1]) || filesize($argv[1]) > 65536) {
    fwrite(STDERR, "Usage: php website/tools/render-local-preview.php overrides.json > preview.html\n");
    exit(2);
}

require dirname(__DIR__) . '/app/bootstrap.php';

try {
    $base = dirname(__DIR__);
    $payload = file_get_contents($argv[1]);
    $overrides = json_decode($payload, true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($overrides) || (array_is_list($overrides) && $overrides !== [])) {
        throw new InvalidArgumentException('Overrides must be a JSON object keyed by approved CMS field IDs');
    }
    $template = file_get_contents($base . '/app/Templates/site-v10.html');
    $registry = file_get_contents($base . '/app/Config/content-fields-v10.json');
    if (!is_string($template) || !is_string($registry)) {
        throw new RuntimeException('Missing template/registry');
    }
    // Prints HTML to stdout; no file/database/hosting mutation.
    echo \Celikom\Website\V10Renderer::render($template, $registry, $overrides);
} catch (\Throwable $exception) {
    // Avoid dumping content or sensitive stack traces into CI logs.
    fwrite(STDERR, "Invalid local preview data, content or template\n");
    exit(1);
}
