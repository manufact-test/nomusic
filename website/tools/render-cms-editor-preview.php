<?php
declare(strict_types=1);
/**
 * CLI-only composite preview for Stage 9 CI. No authentication bypass: this
 * file is outside the public root, never an HTTP endpoint and never deploys.
 */
if(PHP_SAPI!=='cli'||$argc!==2||!is_file($argv[1])||
    filesize($argv[1])===false||filesize($argv[1])>131072){
    fwrite(STDERR,"Usage: php render-cms-editor-preview.php DRAFT_JSON\n");
    exit(2);
}
require dirname(__DIR__).'/app/bootstrap.php';
try {
    $raw=file_get_contents($argv[1]);
    if(!is_string($raw) || (ltrim($raw)[0]??'')!=='{')
        throw new InvalidArgumentException('Invalid JSON');
    $draft=json_decode($raw,true,512,JSON_THROW_ON_ERROR);
    if(!is_array($draft))throw new InvalidArgumentException('Invalid draft');
    $base=dirname(__DIR__);
    $html=file_get_contents($base.'/app/Templates/site-v10.html');
    $manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
    $seed=file_get_contents($base.'/database/seeds/faq-v10.json');
    if(!is_string($html)||!is_string($manifest)||!is_string($seed))
        throw new RuntimeException('Approved v10 assets missing');
    echo \Celikom\Website\CmsEditor::validate($html,$manifest,$seed,$draft);
} catch (\Throwable $e) {
    fwrite(STDERR,"Stage 9 CMS composite preview refused\n");
    exit(1);
}
