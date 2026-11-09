<?php
declare(strict_types=1);
/**
 * Stage 8 private CLI-only installation/footer preview.
 * Payload: {"texts":{"closing.text.02":"..."}, "links":{"footer.link.02":"#how"}}
 * Never an HTTP endpoint or real CMS/publishing backend.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
if ($argc !== 2 || !is_file($argv[1]) ||
    filesize($argv[1]) === false || filesize($argv[1]) > 32768) {
    fwrite(STDERR, "Usage: php website/tools/render-install-footer-preview.php draft.json\n");
    exit(2);
}
require dirname(__DIR__).'/app/bootstrap.php';
try {
    $source = file_get_contents($argv[1]);
    if (!is_string($source) || (ltrim($source)[0] ?? '') !== '{') {
        throw new InvalidArgumentException('Expected JSON object');
    }
    $draft = json_decode($source, true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($draft)) throw new InvalidArgumentException('Invalid Stage 8 JSON');
    foreach (array_keys($draft) as $key) {
        if ($key !== 'texts' && $key !== 'links') {
            throw new InvalidArgumentException('Unexpected Stage 8 draft section');
        }
    }
    $texts = $draft['texts'] ?? [];
    $links = $draft['links'] ?? [];
    if (!is_array($texts) || !is_array($links) ||
        (array_is_list($texts) && $texts !== []) ||
        (array_is_list($links) && $links !== [])) {
        throw new InvalidArgumentException('Stage 8 draft scopes must be objects');
    }
    $base = dirname(__DIR__);
    $html = file_get_contents($base.'/app/Templates/site-v10.html');
    $manifest = file_get_contents($base.'/app/Config/content-fields-v10.json');
    if (!is_string($html) || !is_string($manifest)) {
        throw new RuntimeException('Approved v10 sources unavailable');
    }
    echo \Celikom\Website\InstallFooterDraft::render($html,$manifest,$texts,$links);
} catch (\Throwable $error) {
    fwrite(STDERR, "Stage 8 local installation/footer draft refused\n");
    exit(1);
}
