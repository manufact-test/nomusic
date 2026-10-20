<?php
declare(strict_types=1);

/**
 * Disposable CI-only PHP built-in server router, NOT public_html software.
 * Exactly two read-only HTTP probes may consult the generation selection:
 * /__ci/health (JSON) and /__ci/page (real MySQL-backed approved v10 HTML).
 *
 * "/" and "/admin/" intentionally fall through to the ORIGINAL protected
 * entrypoints, proving that sandbox activity never enables public launch.
 */
$uri=$_SERVER['REQUEST_URI']??'';
$path=parse_url($uri,PHP_URL_PATH);
if (!is_string($path) || !str_starts_with($path,'/__ci/')) {
    return false;
}
header('X-Content-Type-Options: nosniff');
header('X-Robots-Tag: noindex, nofollow, noarchive');
header('Cache-Control: no-store, private');
header('Referrer-Policy: no-referrer');
header('X-Frame-Options: DENY');

$public=realpath(dirname(__DIR__,2).'/public');
$docroot=realpath((string)($_SERVER['DOCUMENT_ROOT']??''));
$private=getenv('CELIKOM_SITE_CI_GENERATION_ROOT');
if (PHP_SAPI!=='cli-server' ||
    getenv('CI')!=='true' ||
    getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
    getenv('CELIKOM_SITE_HTTP_SANDBOX')!=='1' ||
    !is_string($public) || !is_string($docroot) || $docroot!==$public ||
    !is_string($private) || $private==='' ||
    ($_SERVER['REMOTE_ADDR']??'')!=='127.0.0.1' ||
    !preg_match('/^127\\.0\\.0\\.1(?::[0-9]{1,5})?$/D',
        (string)($_SERVER['HTTP_HOST']??''))) {
    http_response_code(503);
    echo 'CI generation probe disabled';
    return true;
}
if (($_SERVER['REQUEST_METHOD']??'')!=='GET') {
    http_response_code(405);
    header('Allow: GET');
    echo 'Read-only CI diagnostics';
    return true;
}
if (!in_array($path,['/__ci/health','/__ci/page'],true) ||
    $uri!==$path) {
    http_response_code(404);
    echo 'Not found';
    return true;
}
require dirname(__DIR__,2).'/app/bootstrap.php';
try {
    $cfg=\Celikom\Website\CmsConfig::databaseSettings();
    $gate=\Celikom\Website\CmsWriteQuiescence::snapshot($public);
    try {
        $snapshot=\Celikom\Website\CmsSandboxGeneration::active(
            $cfg,$private,$public,$gate
        );
        $record=$snapshot['record'];
        $health=$snapshot['health'];
        $db=\Celikom\Website\Database::connect([...$cfg,'dbname'=>$record['database']]);
        if (\Celikom\Website\CmsRevisions::publishedId($db)===null) {
            throw new RuntimeException('Unpublished test CMS');
        }
        $base=dirname(__DIR__,2);
        $template=file_get_contents($base.'/app/Templates/site-v10.html');
        $manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
        $faq=file_get_contents($base.'/database/seeds/faq-v10.json');
        if (!is_string($template) || !is_string($manifest) ||
            !is_string($faq)) {
            throw new RuntimeException('Missing approved v10 fixture');
        }
        $html=\Celikom\Website\CmsRevisions::publishedPage(
            $db,$template,$manifest,$faq
        );
        if ($path==='/__ci/health') {
            header('Content-Type: application/json; charset=utf-8');
            echo json_encode([
                'healthy'=>true,
                'generation'=>$record['generation'],
                'schema_version'=>$health['schema_version'],
                'media_files'=>$health['media_files'],
                'html_sha256'=>hash('sha256',$html),
            ],JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES);
        } else {
            header('Content-Type: text/html; charset=utf-8');
            echo $html;
        }
    } finally {
        $gate->release();
    }
} catch (\Throwable $error) {
    error_log('CELIKOM offline-only generation HTTP probe failed');
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Sandbox generation is unhealthy';
}
return true;
