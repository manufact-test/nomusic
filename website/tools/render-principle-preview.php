<?php
declare(strict_types=1);

/** Stage 5 offline, private CLI-only preview. Not a route, admin or publisher. */
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
if ($argc !== 2 || !is_file($argv[1]) || filesize($argv[1]) > 32768) {
    fwrite(STDERR,"Usage: php website/tools/render-principle-preview.php draft.json\n");
    exit(2);
}
require dirname(__DIR__).'/app/bootstrap.php';
try {
    $data = file_get_contents($argv[1]);
    $overrides = json_decode($data, true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($overrides) || (array_is_list($overrides) && $overrides !== [])) {
        throw new InvalidArgumentException('JSON object required');
    }
    $base=dirname(__DIR__);
    $html=file_get_contents($base.'/app/Templates/site-v10.html');
    $manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
    if (!is_string($html) || !is_string($manifest)) {
        throw new RuntimeException('Approved source missing');
    }
    echo \Celikom\Website\PrincipleDraft::render($html,$manifest,$overrides);
} catch (\Throwable $error) {
    fwrite(STDERR,"Stage 5 private preview rejected unsafe or invalid content\n");
    exit(1);
}
