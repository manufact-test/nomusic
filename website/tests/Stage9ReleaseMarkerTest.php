<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\CmsReleaseGate;

function gateAssert(bool $ok,string $message):void {
    if(!$ok)throw new RuntimeException('Stage 9 private release authorization: '.$message);
}

$dir=sys_get_temp_dir().'/celikom-private-gate-'.bin2hex(random_bytes(8));
if(!mkdir($dir,0700))throw new RuntimeException('Could not make private fixture dir');
$path=$dir.'/release-approved.php';
$other=$dir.'/untrusted.php';
try {
    gateAssert(!CmsReleaseGate::approved($dir),'missing marker unexpectedly allowed');
    gateAssert(!CmsReleaseGate::approved($dir.'/not-created'),'missing app directory allowed');
    file_put_contents($path,'');
    chmod($path,0600);
    gateAssert(!CmsReleaseGate::approved($dir),'empty marker allowed');
    file_put_contents($path,"<?php\nreturn true;\n");
    gateAssert(!CmsReleaseGate::approved($dir),'arbitrary PHP allowed');
    file_put_contents($path,"<?php\nreturn 'CELIKOM_SITE_AND_CMS_APPROVED_STAGE10';\r\n");
    gateAssert(!CmsReleaseGate::approved($dir),'modified line endings allowed');
    $expected="<?php\nreturn 'CELIKOM_SITE_AND_CMS_APPROVED_STAGE10';\n";
    file_put_contents($path,$expected);
    chmod($path,0644);
    gateAssert(!CmsReleaseGate::approved($dir),'world-readable approval marker allowed');
    chmod($path,0600);
    gateAssert(CmsReleaseGate::approved($dir),'strict private owner approval was refused');
    file_put_contents($path,$expected.' ');
    gateAssert(!CmsReleaseGate::approved($dir),'trailing data allowed');
    unlink($path);
    file_put_contents($other,$expected);
    chmod($other,0600);
    if(!symlink($other,$path))throw new RuntimeException('Cannot set up symlink fixture');
    gateAssert(!CmsReleaseGate::approved($dir),'symlinked authorization accepted');
    unlink($path);
    // Evaluation of the supposed PHP marker would cause side effects. Static
    // inspection of untrusted files MUST never evaluate or include them.
    $canary=$dir.'/executed.txt';
    file_put_contents($path,"<?php file_put_contents(".
        var_export($canary,true).",'unsafe'); return 'CELIKOM_SITE_AND_CMS_APPROVED_STAGE10';\n");
    chmod($path,0600);
    gateAssert(!CmsReleaseGate::approved($dir),'executable marker accepted');
    gateAssert(!file_exists($canary),'authorization inspected by executing attacker PHP');
    echo "Stage9: strict private release token; empty, modified, public, symlink and PHP injection refused — PASS\n";
} finally {
    if(is_link($path)||is_file($path))unlink($path);
    if(is_file($other))unlink($other);
    if(isset($canary)&&is_file($canary))unlink($canary);
    rmdir($dir);
}
