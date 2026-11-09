<?php
declare(strict_types=1);
/**
 * Stage 7 developer-only combined trust/FAQ preview.
 * Payload: {"texts":{"transparency.text.02":"..."}, "faq":{"updates":{...}}}
 * Absolutely no HTTP publishing, database writes or authenticated CMS yet.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
if ($argc !== 2 || !is_file($argv[1]) ||
    filesize($argv[1]) === false || filesize($argv[1]) > 65536) {
    fwrite(STDERR, "Usage: php website/tools/render-trust-preview.php draft.json\n");
    exit(2);
}
require dirname(__DIR__) . '/app/bootstrap.php';
try {
    $source = file_get_contents($argv[1]);
    if (!is_string($source) || (ltrim($source)[0] ?? '') !== '{') {
        throw new InvalidArgumentException('Expected JSON object');
    }
    $draft = json_decode($source, true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($draft)) throw new InvalidArgumentException('Invalid JSON draft');
    foreach (array_keys($draft) as $key) {
        if ($key !== 'texts' && $key !== 'faq') {
            throw new InvalidArgumentException('Unexpected draft scope');
        }
    }
    $texts = $draft['texts'] ?? [];
    $faq = $draft['faq'] ?? [];
    if (!is_array($texts) || !is_array($faq) ||
        (array_is_list($texts) && $texts !== []) ||
        (array_is_list($faq) && $faq !== [])) {
        throw new InvalidArgumentException('Stage 7 draft sections must be objects');
    }
    $base = dirname(__DIR__);
    $html = file_get_contents($base . '/app/Templates/site-v10.html');
    $schema = file_get_contents($base . '/app/Config/content-fields-v10.json');
    $seed = file_get_contents($base . '/database/seeds/faq-v10.json');
    if (!is_string($html) || !is_string($schema) || !is_string($seed)) {
        throw new RuntimeException('Approved source unavailable');
    }
    echo \Celikom\Website\TrustDraft::render($html, $schema, $seed, $texts, $faq);
} catch (\Throwable $error) {
    fwrite(STDERR, "Stage 7 local trust/FAQ draft refused\n");
    exit(1);
}
