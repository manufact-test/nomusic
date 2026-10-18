<?php
declare(strict_types=1);

/**
 * CELIKOM website (Stage 3 shell).
 *
 * The approved v10 page is kept in the private app template, not copied to
 * public_html with screenshot data. The live web entry is intentionally
 * blocked until the small CMS and owner-approved joint release are ready.
 */
header('Content-Type: text/html; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: strict-origin-when-cross-origin');
header('X-Frame-Options: DENY');
header('X-Robots-Tag: noindex, nofollow, noarchive');
header('Cache-Control: no-store');

$domainRoot = dirname(__DIR__);
$privateApp = $domainRoot . '/celikom-private/app';

// Explicit *local* preview only (PHP built-in server + env switch).
$localPreview = PHP_SAPI === 'cli-server'
    && getenv('CELIKOM_LOCAL_PREVIEW') === '1';
if ($localPreview) {
    $privateApp = dirname(__DIR__) . '/app';
}

// Production always requires an approved CMS and protected release state.
$approved = !$localPreview
    && is_file($privateApp . '/bootstrap.php')
    && is_file(__DIR__ . '/admin/index.php');
if ($approved) {
    require_once $privateApp . '/bootstrap.php';
    $productionApproved = \Celikom\Website\CmsReleaseGate::approved($privateApp);
    $stagingApproved = \Celikom\Website\CmsStagingGate::approved($privateApp);
    $approved = $productionApproved || $stagingApproved;
    if ($stagingApproved && !$productionApproved) {
        \Celikom\Website\CmsStagingHttpAuth::enforce($privateApp);
    }
}

if (!$localPreview && !$approved) {
    http_response_code(503);
    header('Retry-After: 86400');
    echo '<!doctype html><html lang="ru"><meta charset="utf-8"><title>CELIKOM — подготовка сайта</title><p>CELIKOM готовится к запуску.</p></html>';
    exit;
}

// Isolated A/B clips for the password-protected owner-review site only.
// Fixed private paths: no user-provided filename, no media DB, no writes,
// and nothing in the live CELIKOM extension/replacement library.
if (!$localPreview && $approved && isset($_GET['demo_audio'])) {
    try {
        if (!$stagingApproved || $productionApproved ||
            !in_array($_SERVER['REQUEST_METHOD'] ?? '', ['GET','HEAD'], true)) {
            throw new RuntimeException('Audio demo is staging-only');
        }
        $names = ['service'=>'service.mp3', 'restored'=>'restored.mp3'];
        $mode=$_GET['demo_audio'];
        if (!is_string($mode) || !isset($names[$mode])) {
            throw new RuntimeException('Unknown demo audio variant');
        }
        $path=$domainRoot.'/celikom-private/demo-audio/clips/'.$names[$mode];
        if (!is_file($path) || is_link($path) || !is_readable($path)) {
            throw new RuntimeException('Demo clip unavailable');
        }
        $size=filesize($path);
        if (!is_int($size) || $size<1000 || $size>2097152) {
            throw new RuntimeException('Invalid demo clip size');
        }
        $start=0;
        $end=$size-1;
        $partial=false;
        if (isset($_SERVER['HTTP_RANGE'])) {
            $range=$_SERVER['HTTP_RANGE'];
            if (!is_string($range) ||
                !preg_match('/^bytes=(\d+)-(\d*)$/D',$range,$match)) {
                header('Content-Range: bytes */'.$size);
                http_response_code(416);
                exit;
            }
            $start=(int)$match[1];
            $end=$match[2]==='' ? $end : min($end,(int)$match[2]);
            if ($start>$end || $start>=$size) {
                header('Content-Range: bytes */'.$size);
                http_response_code(416);
                exit;
            }
            $partial=true;
        }
        $stream=fopen($path,'rb');
        if ($stream===false || fseek($stream,$start)!==0) {
            throw new RuntimeException('Cannot read demo clip');
        }
        header('Content-Type: audio/mpeg');
        header('Accept-Ranges: bytes');
        header('Content-Length: '.($end-$start+1));
        header('Cache-Control: private, no-store');
        if ($partial) {
            http_response_code(206);
            header('Content-Range: bytes '.$start.'-'.$end.'/'.$size);
        }
        if (($_SERVER['REQUEST_METHOD'] ?? '')==='GET') {
            $remaining=$end-$start+1;
            while ($remaining>0 && !feof($stream)) {
                $chunk=fread($stream,min(65536,$remaining));
                if ($chunk===false || $chunk==='')break;
                echo $chunk;
                $remaining-=strlen($chunk);
            }
        }
        fclose($stream);
    } catch (\Throwable $error) {
        error_log('CELIKOM: private demo audio unavailable');
        http_response_code(404);
    }
    exit;
}

// Exact approved v10 popup, served only within password-protected staging.
// The original screenshot stays in the CMS private media store, never public_html.
if (!$localPreview && $approved && ($_GET['v10_popup'] ?? '') === 'approved') {
    try {
        if (!$stagingApproved || $productionApproved) {
            throw new RuntimeException('Private v10 media is staging-only');
        }
        $storage = getenv('CELIKOM_SITE_MEDIA_DIR');
        if (!is_string($storage) || $storage === '') {
            throw new RuntimeException('Private media storage not configured');
        }
        $pdo = \Celikom\Website\Database::connect(
            \Celikom\Website\CmsConfig::databaseSettings()
        );
        $query = $pdo->prepare(
            "SELECT id FROM media_assets WHERE sha256=? AND mime_type='image/png' AND is_active=1 ORDER BY id DESC LIMIT 1"
        );
        $query->execute(['0366d4f32b0edf67c2300b372202e5604999fa9e9dbb8f2ebfd295aed6fcf1fc']);
        $imageId = $query->fetchColumn();
        if ($imageId === false) {
            http_response_code(404);
            exit;
        }
        $image = \Celikom\Website\CmsMediaStore::privatePreview(
            $pdo, (int)$imageId, $storage, __DIR__
        );
        if ($image['mime'] !== 'image/png') {
            throw new RuntimeException('Original popup MIME mismatch');
        }
        header('Content-Type: image/png');
        header('Content-Length: '.strlen($image['body']));
        header('Cache-Control: private, no-store');
        echo $image['body'];
    } catch (\Throwable $error) {
        error_log('CELIKOM: approved private v10 popup unavailable');
        http_response_code(404);
    }
    exit;
}

$bootstrap = $privateApp . '/bootstrap.php';
$template = $privateApp . '/Templates/site-v10.html';
if (!is_file($bootstrap) || !is_file($template)) {
    error_log('CELIKOM website: required private application files are missing');
    http_response_code(503);
    echo 'CELIKOM временно недоступен.';
    exit;
}
$manifestPath = $privateApp . '/Config/content-fields-v10.json';
$faqSeedPath = $localPreview
    ? dirname(__DIR__) . '/database/seeds/faq-v10.json'
    : $domainRoot . '/celikom-private/database/seeds/faq-v10.json';
if (!is_file($manifestPath) || !is_file($faqSeedPath)) {
    error_log('CELIKOM website: verified CMS content schema is unavailable');
    http_response_code(503);
    echo 'CELIKOM временно недоступен.';
    exit;
}
require_once $bootstrap;
try {
    $trustedHtml = file_get_contents($template);
    $contentSchema = file_get_contents($manifestPath);
    $faqSeed = file_get_contents($faqSeedPath);
    if (!is_string($trustedHtml) || !is_string($contentSchema) || !is_string($faqSeed)) {
        throw new RuntimeException('Missing trusted template and content schema');
    }
    if ($localPreview) {
        // Explicit developer-only preview remains canonical v10 and requires
        // neither a database nor a release approval marker.
        $verifiedPage = \Celikom\Website\V10Renderer::render($trustedHtml, $contentSchema, []);
        echo \Celikom\Website\FaqV10Renderer::render($verifiedPage, $faqSeed, []);
    } else {
        // Only AFTER the separate Stage 10 release-approved marker exists,
        // read a single immutable MySQL revision. A missing database, empty
        // publication pointer, corrupt snapshot or incompatible v10 schema
        // must fail closed, not leak a draft or silently fall back.
        $pdo = \Celikom\Website\Database::connect(
            \Celikom\Website\CmsConfig::databaseSettings()
        );
        if (\Celikom\Website\CmsRevisions::publishedId($pdo) === null) {
            throw new RuntimeException('No reviewed CMS revision has been published');
        }
        $publishedHtml = \Celikom\Website\CmsRevisions::publishedPage(
            $pdo, $trustedHtml, $contentSchema, $faqSeed
        );
        echo \Celikom\Website\CmsV10OwnerMotion::apply($publishedHtml);
    }
} catch (\Throwable $error) {
    error_log('CELIKOM website: protected content render failed');
    http_response_code(503);
    echo 'CELIKOM временно недоступен.';
}
