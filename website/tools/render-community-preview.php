<?php
declare(strict_types=1);

/**
 * Stage 6 community/reward copy, local CLI preview ONLY.
 * Does not accept policy changes, upload music or submit anything.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
if ($argc !== 2 || !is_file($argv[1]) || filesize($argv[1]) > 32768) {
    fwrite(STDERR, "Usage: php website/tools/render-community-preview.php draft.json\n");
    exit(2);
}
require dirname(__DIR__).'/app/bootstrap.php';
try {
    $source = file_get_contents($argv[1]);
    $draft = json_decode($source, true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($draft) || (array_is_list($draft) && $draft !== [])) {
        throw new InvalidArgumentException('Expected JSON object');
    }
    $base = dirname(__DIR__);
    $html = file_get_contents($base.'/app/Templates/site-v10.html');
    $schema = file_get_contents($base.'/app/Config/content-fields-v10.json');
    if (!is_string($html) || !is_string($schema)) throw new RuntimeException('Missing approved source');
    echo \Celikom\Website\CommunityDraft::render($html, $schema, $draft);
} catch (\Throwable $problem) {
    fwrite(STDERR, "Stage 6 local community draft refused\n");
    exit(1);
}
