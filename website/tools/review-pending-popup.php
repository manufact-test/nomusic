<?php
declare(strict_types=1);

/**
 * Stage 9 PRIVATE review aid. Run only from CLI with separate website DB
 * credentials and CELIKOM_SITE_MEDIA_DIR outside public_html.
 * Does not grant legal permission, publish media or change release state.
 */
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsConfig;
use Celikom\Website\CmsMediaReleasePreflight;
use Celikom\Website\Database;

$directory=getenv('CELIKOM_SITE_MEDIA_DIR');
if(!is_string($directory) || $directory==='' || !is_dir($directory)) {
    fwrite(STDERR,"Private CMS storage is not configured.\n");
    exit(2);
}
try {
    $pdo=Database::connect(CmsConfig::databaseSettings());
    $review=CmsMediaReleasePreflight::pending(
        $pdo,$directory,dirname(__DIR__).'/public'
    );
    echo json_encode($review,
        JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR),PHP_EOL;
} catch(\Throwable $e) {
    // Do not leak filesystem paths, asset bytes or DB connection metadata.
    fwrite(STDERR,"Private popup review unavailable; nothing was approved.\n");
    exit(1);
}
