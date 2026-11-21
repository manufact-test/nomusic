<?php
declare(strict_types=1);

/**
 * Read-only CLI handoff contract for a future Stage 9 CMS editor.
 * It publishes nothing and cannot be called via the website document root.
 */
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
if ($argc !== 1) {
    fwrite(STDERR, "Usage: php website/tools/list-first-screen-fields.php\n");
    exit(2);
}
require dirname(__DIR__) . '/app/bootstrap.php';

try {
    $manifest = file_get_contents(dirname(__DIR__) . '/app/Config/content-fields-v10.json');
    if (!is_string($manifest)) throw new RuntimeException('Content schema unavailable');
    $fields = \Celikom\Website\FirstScreenFieldCatalog::fields($manifest);
    echo json_encode([
        'contract' => 'celikom-first-screen-v10-stage4',
        'preview_only' => true,
        'public_admin_available' => false,
        'requires_stage9_authentication' => true,
        'fields' => array_values($fields),
    ], JSON_THROW_ON_ERROR | JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), "\n";
} catch (\Throwable $error) {
    fwrite(STDERR, "Stage 4 field contract unavailable\n");
    exit(1);
}
