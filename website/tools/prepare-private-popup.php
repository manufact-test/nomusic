<?php
declare(strict_types=1);
/**
 * CLI-only Stage 9 PRIVATE screenshot derivative rehearsal.
 * Usage: php prepare-private-popup.php PRIVATE_MEDIA_DIR PRIVATE_REVIEW_DIR PUBLIC_ROOT
 * Requires separate website DB environment configuration and ext-gd.
 * Leaves an unapproved PNG in PRIVATE_REVIEW_DIR, never opens the public site.
 */
if(PHP_SAPI!=='cli')exit(2);
require dirname(__DIR__).'/app/bootstrap.php';
if($argc!==4) {
    fwrite(STDERR,"Usage: prepare-private-popup.php MEDIA_DIR REVIEW_DIR PUBLIC_ROOT\n");
    exit(2);
}
try {
    // Treat private review PNG generation as a writer for shared backup freeze.
    $lease=\Celikom\Website\CmsWriteQuiescence::writer($argv[3]);
    $pdo=\Celikom\Website\Database::connect(
        \Celikom\Website\CmsConfig::databaseSettings()
    );
    $report=\Celikom\Website\CmsMediaDerivative::preparePending(
        $pdo,$argv[1],$argv[2],$argv[3]
    );
    echo json_encode($report,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT),"\n";
} catch(\Throwable $e) {
    // No filesystem paths, private bytes, credentials or private data.
    fwrite(STDERR,"Private derivative review unavailable; no media was approved.\n");
    exit(1);
}
