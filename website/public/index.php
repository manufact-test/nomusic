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
        echo \Celikom\Website\CmsOwnerPolish::apply($publishedHtml, __DIR__);
    }
} catch (\Throwable $error) {
    error_log('CELIKOM website: protected content render failed');
    http_response_code(503);
    echo 'CELIKOM временно недоступен.';
}
