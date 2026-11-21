<?php
declare(strict_types=1);
/**
 * Isolated CI MySQL release readiness checks. No release, server deployment,
 * private screenshot, or production database connection.
 */
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsReleaseReadiness;
use Celikom\Website\Database;
function readyAssert(bool $ok,string $reason):void {
    if(!$ok)throw new RuntimeException('Stage 10 release audit: '.$reason);
}
if(getenv('CI')!=='true')throw new RuntimeException('Readiness integration test requires CI');
$cfg=CmsConfig::databaseSettings();
if($cfg['dbname']!=='celikom_site_test' || $cfg['host']!=='127.0.0.1') {
    throw new RuntimeException('Readiness integration test forbids non-CI database');
}
$pdo=Database::connect($cfg);
$root=dirname(__DIR__);
$app=$root.'/app';
$faq=$root.'/database/seeds/faq-v10.json';
$originalPublic=$root.'/public';
$temp=sys_get_temp_dir().'/celikom-stage10-readiness-'.bin2hex(random_bytes(8));
$public=$temp.'/public';
$media=$public.'/media';
$shadowApp=$temp.'/private-app';
$shadowTpl=$shadowApp.'/Templates';
$shadowConfig=$shadowApp.'/Config';
if(!mkdir($temp,0700) || !mkdir($public,0700) || !mkdir($media,0700) ||
    !mkdir($shadowApp,0700) || !mkdir($shadowTpl,0700) ||
    !mkdir($shadowConfig,0700)) {
    throw new RuntimeException('Cannot make private readiness fixture');
}
$popup=$media.'/celikom-popup-approved.png';
try {
    $report=CmsReleaseReadiness::inspect($pdo,$app,$faq,$originalPublic);
    readyAssert($report['ready']===false,'audit opened release without owner consent');
    readyAssert($report['checks']['approved_v10_template']===true,
        'approved v10 template changed');
    readyAssert($report['checks']['draft_is_valid']===true,
        'saved CMS draft is invalid');
    readyAssert($report['checks']['active_owner_exists']===true,
        'single disposable CI owner missing');
    readyAssert($report['checks']['published_revision_exists']===true &&
        $report['checks']['published_revision_valid']===true,
        'existing CI publication not valid');
    readyAssert($report['checks']['owner_reviewed_popup_bytes_match']===false &&
        in_array('approved_popup_bytes_or_review_missing',$report['blockers'],true),
        'missing rights-reviewed image was silently accepted');
    readyAssert(in_array('full_database_backup_and_restore_pending',$report['blockers'],true) &&
        in_array('production_file_rollback_pending',$report['blockers'],true) &&
        in_array('owner_joint_release_approval_pending',$report['blockers'],true),
        'unverified production prerequisites were waived');

    $fixture=base64_decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true
    );
    readyAssert(is_string($fixture) && strlen($fixture)>30,'synthetic PNG fixture');
    file_put_contents($popup,$fixture);
    chmod($popup,0600);
    $digest=hash('sha256',$fixture);
    $good=CmsReleaseReadiness::inspect($pdo,$app,$faq,$public,$digest);
    readyAssert($good['checks']['owner_reviewed_popup_bytes_match']===true &&
        $good['ready']===false,'valid bytes must not bypass owner and DB signoffs');
    $wrong=CmsReleaseReadiness::inspect($pdo,$app,$faq,$public,str_repeat('a',64));
    readyAssert($wrong['checks']['owner_reviewed_popup_bytes_match']===false,
        'wrong SHA accepted');
    file_put_contents($popup,'not an image');
    readyAssert(CmsReleaseReadiness::inspect($pdo,$app,$faq,$public,
        hash('sha256','not an image'))['checks']['owner_reviewed_popup_bytes_match']===false,
        'non-image file accepted even with matching digest');

    unlink($popup);
    file_put_contents($temp.'/outside.png',$fixture);
    symlink($temp.'/outside.png',$popup);
    readyAssert(CmsReleaseReadiness::inspect($pdo,$app,$faq,$public,$digest)
        ['checks']['owner_reviewed_popup_bytes_match']===false,
        'symlinked popup allowed');

    copy($app.'/Templates/site-v10.html',$shadowTpl.'/site-v10.html');
    copy($app.'/Config/content-fields-v10.json',$shadowConfig.'/content-fields-v10.json');
    file_put_contents($shadowTpl.'/site-v10.html',
        (string)file_get_contents($shadowTpl.'/site-v10.html').'tampered');
    $corrupt=CmsReleaseReadiness::inspect($pdo,$shadowApp,$faq,$public,$digest);
    readyAssert($corrupt['checks']['approved_v10_template']===false &&
        in_array('approved_v10_template_changed',$corrupt['blockers'],true),
        'edited v10 was accepted');
    $pdo->beginTransaction();
    try {
        $pdo->exec("UPDATE admin_users SET is_active=0 WHERE username='owner'");
        $disabled=CmsReleaseReadiness::inspect($pdo,$app,$faq,$public,$digest);
        readyAssert($disabled['checks']['active_owner_exists']===false,
            'inactive owner accepted');
    } finally {
        $pdo->rollBack();
    }
    readyAssert(CmsReleaseReadiness::inspect($pdo,$app,$faq,$originalPublic)
        ['checks']['active_owner_exists']===true,'CI owner was mutated');
    echo "Stage10: CMS/MySQL read-only audit, v10 integrity, owner and popup tampering, production blockers — PASS\n";
} finally {
    foreach([$popup,$temp.'/outside.png',
        $shadowTpl.'/site-v10.html',$shadowConfig.'/content-fields-v10.json'] as $file) {
        if(is_file($file)||is_link($file))unlink($file);
    }
    foreach([$media,$public,$shadowTpl,$shadowConfig,$shadowApp,$temp] as $dir) {
        if(is_dir($dir))rmdir($dir);
    }
}
