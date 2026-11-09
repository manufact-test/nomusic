<?php
declare(strict_types=1);
/**
 * CLI only, READ-ONLY Stage 10 website+CMS readiness report.
 *
 * Production: CELIKOM_SITE_DB_* environment points to a dedicated site DB.
 * Optional CELIKOM_SITE_APPROVED_POPUP_SHA256 is supplied outside GitHub by
 * the rights-review owner; it is NOT proof of legal rights by itself.
 *
 * php website/tools/check-release-readiness.php [PRIVATE_APP_DIR FAQ_SEED PUBLIC_ROOT]
 *
 * Exit 0: structural audit completed (release may still be BLOCKED).
 * Exit 1: structural audit couldn't run. This program never opens a site.
 */
if (PHP_SAPI !== 'cli') exit(2);
require dirname(__DIR__).'/app/bootstrap.php';
try {
    if ($argc === 1) {
        $root=dirname(__DIR__);
        $app=$root.'/app';
        $faq=$root.'/database/seeds/faq-v10.json';
        $public=$root.'/public';
    } elseif ($argc === 4) {
        $app=$argv[1];
        $faq=$argv[2];
        $public=$argv[3];
    } else {
        fwrite(STDERR,"Usage: php check-release-readiness.php [APP FAQ_SEED PUBLIC]\n");
        exit(2);
    }
    $pdo=\Celikom\Website\Database::connect(
        \Celikom\Website\CmsConfig::databaseSettings()
    );
    $sha=getenv('CELIKOM_SITE_APPROVED_POPUP_SHA256');
    $report=\Celikom\Website\CmsReleaseReadiness::inspect(
        $pdo,$app,$faq,$public,is_string($sha)?$sha:null
    );
    echo json_encode($report,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)."\n";
} catch(\Throwable $e) {
    fwrite(STDERR,"Stage 10 CMS readiness audit unavailable; no release approved\n");
    exit(1);
}
