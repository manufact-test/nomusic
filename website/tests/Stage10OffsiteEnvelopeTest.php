<?php
declare(strict_types=1);
/** Stage 10: isolated encrypted offsite transport + real MySQL/media replay. */
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsConsistentBackup;
use Celikom\Website\CmsOffsiteEnvelope;
use Celikom\Website\CmsSandboxRecovery;
use Celikom\Website\CmsWriteQuiescence;
use Celikom\Website\CmsMediaStore;
use Celikom\Website\Database;

function offsiteCheck(bool $valid,string $message):void {
    if (!$valid) throw new RuntimeException('CI offsite CMS: '.$message);
}
function offsiteDeny(callable $operation,string $message):void {
    try { $operation(); } catch (\Throwable $e) {return;}
    throw new RuntimeException('Offsite operation unexpectedly succeeded: '.$message);
}
$cfg=CmsConfig::databaseSettings();
if (getenv('CI')!=='true'||getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1'||
    $cfg['host']!=='127.0.0.1'||$cfg['dbname']!=='celikom_site_test') {
    throw new RuntimeException('Offsite drill requires disposable CI MySQL');
}
$root=dirname(__DIR__);
$public=$root.'/public';
$pdo=Database::connect($cfg);
$base=sys_get_temp_dir().'/celikom-offsite-ci-'.bin2hex(random_bytes(10));
$bundle=$base.'/bundle';$media=$base.'/media';$transport=$base.'/transport';
$recovered=$base.'/recovered';$sandbox=$base.'/sandbox';
foreach ([$base,$bundle,$media,$transport,$recovered,$sandbox] as $dir) {
    if (!mkdir($dir,0700)) throw new RuntimeException('Cannot create isolated offsite test folder');
}
$fullDbKey=random_bytes(32);
$offsiteKey=random_bytes(32);
$keyName=bin2hex(random_bytes(20)).'.png';
$picture=base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true);
offsiteCheck(is_string($picture)&&strlen($picture)>=30,'synthetic PNG absent');
file_put_contents($media.'/'.$keyName,$picture);chmod($media.'/'.$keyName,0600);
putenv('CELIKOM_SITE_WRITE_GATE_FILE='.$base.'/.celikom-cms-writes.lock');
$asset=null;$lease=null;$restored=null;$manifest=null;
try {
    offsiteDeny(fn()=>CmsOffsiteEnvelope::keyFromEnv($fullDbKey),
        'key absent');
    putenv('CELIKOM_SITE_OFFSITE_KEY='.base64_encode($offsiteKey));
    offsiteCheck(CmsOffsiteEnvelope::keyFromEnv($fullDbKey)===$offsiteKey,
        'independent key not accepted');
    putenv('CELIKOM_SITE_OFFSITE_KEY='.base64_encode($fullDbKey));
    offsiteDeny(fn()=>CmsOffsiteEnvelope::keyFromEnv($fullDbKey),
        'full DB key was reused as transport key');
    putenv('CELIKOM_SITE_OFFSITE_KEY='.base64_encode($offsiteKey));

    $pdo->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,'.
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)')
        ->execute(['site-private/'.$keyName,'offsite-fixture.png','image/png',
            hash('sha256',$picture),1,1,'CI sealed media',1]);
    $asset=(int)$pdo->lastInsertId();
    offsiteCheck($asset>0,'source media SQL missing');
    $lease=CmsWriteQuiescence::snapshot($public);
    $capture=CmsConsistentBackup::capture($pdo,$bundle,$media,$public,$fullDbKey,$lease);
    $manifest=$capture['manifest'];
    $lease->release();

    offsiteDeny(fn()=>CmsOffsiteEnvelope::seal(
        $manifest,$fullDbKey,$fullDbKey,$transport,$public),
        'reused DB key');
    offsiteDeny(fn()=>CmsOffsiteEnvelope::seal(
        $manifest,$fullDbKey,$offsiteKey,$public,$public),
        'plaintext or ciphertext placed in web root');
    offsiteDeny(fn()=>CmsOffsiteEnvelope::seal(
        $manifest,$fullDbKey,$offsiteKey,$bundle,$public),
        'sealing beside the plaintext backup');
    offsiteCheck(scandir($transport)===['.','..'],'invalid seal created output');

    $sealed=CmsOffsiteEnvelope::seal(
        $manifest,$fullDbKey,$offsiteKey,$transport,$public);
    $contents=(string)file_get_contents($sealed);
    offsiteCheck(is_file($sealed)&&(fileperms($sealed)&0777)===0600 &&
        count(array_diff(scandir($transport),['.','..']))===1 &&
        !str_contains($contents,'site-private/') &&
        !str_contains($contents,$keyName) &&
        !str_contains($contents,'password_hash') &&
        !str_contains($contents,'celikom-site-content-backup-v1') &&
        !str_contains($contents,'published_revision_id') &&
        str_starts_with($contents,"CELIKOM_SITE_OFFSITE_V1\n"),
        'offsite transport exposed plaintext or failed encryption');
    offsiteCheck(CmsOffsiteEnvelope::inspect($sealed,$offsiteKey)['encrypted']===true,
        'sealed archive verification failed');

    offsiteDeny(fn()=>CmsOffsiteEnvelope::inspect($sealed,random_bytes(32)),
        'wrong independent encryption key');
    offsiteDeny(fn()=>CmsOffsiteEnvelope::unseal(
        $sealed,$fullDbKey,random_bytes(32),$recovered,$public),
        'wrong offsite key extracted plaintext');
    offsiteCheck(scandir($recovered)===['.','..'],'wrong key left private outputs');
    offsiteDeny(fn()=>CmsOffsiteEnvelope::unseal(
        $sealed,random_bytes(32),$offsiteKey,$recovered,$public),
        'wrong underlying MySQL archive key');
    offsiteCheck(scandir($recovered)===['.','..'],'wrong DB key leaked plaintext');

    $bad=$transport.'/celikom-offsite-20261018-120000-'.bin2hex(random_bytes(12)).'.sbox';
    $tampered=$contents;
    $i=min(150,strlen($tampered)-15);
    $tampered[$i]=chr(ord($tampered[$i])^1);
    file_put_contents($bad,$tampered);chmod($bad,0600);
    offsiteDeny(fn()=>CmsOffsiteEnvelope::unseal(
        $bad,$fullDbKey,$offsiteKey,$recovered,$public),'modified ciphertext');
    file_put_contents($bad,substr($contents,0,-12));
    offsiteDeny(fn()=>CmsOffsiteEnvelope::unseal(
        $bad,$fullDbKey,$offsiteKey,$recovered,$public),'truncated final authentication');
    file_put_contents($bad,$contents.'extra');
    offsiteDeny(fn()=>CmsOffsiteEnvelope::unseal(
        $bad,$fullDbKey,$offsiteKey,$recovered,$public),'trailing unauthenticated junk');
    unlink($bad);
    offsiteCheck(scandir($recovered)===['.','..'],'tampered archives left plaintext');

    chmod($sealed,0644);
    offsiteDeny(fn()=>CmsOffsiteEnvelope::inspect($sealed,$offsiteKey),
        'world-readable transport');
    chmod($sealed,0600);
    $target=$transport.'/poison';
    file_put_contents($target,'untouched');chmod($target,0600);
    $sym=$transport.'/celikom-offsite-20261018-120000-'.bin2hex(random_bytes(12)).'.sbox';
    symlink($target,$sym);
    offsiteDeny(fn()=>CmsOffsiteEnvelope::inspect($sym,$offsiteKey),
        'symlinked ciphertext');
    offsiteCheck(file_get_contents($target)==='untouched',
        'symlink attack mutated foreign file');
    unlink($sym);unlink($target);
    putenv('CI=false');
    offsiteDeny(fn()=>CmsOffsiteEnvelope::inspect($sealed,$offsiteKey),
        'non-CI archive opened');
    putenv('CI=true');

    $open=CmsOffsiteEnvelope::unseal(
        $sealed,$fullDbKey,$offsiteKey,$recovered,$public
    );
    $privateDir=dirname($open['manifest']);
    offsiteCheck($open['encrypted_transport']===true &&
        $open['report']['consistent']===true &&
        $open['report']['media_files']===1 &&
        realpath($privateDir)!==realpath($public) &&
        count(array_diff(scandir($privateDir),['.','..']))===3,
        'offsite restore did not recover a private consistent pair');
    foreach (glob($privateDir.'/*')?:[] as $component) {
        offsiteCheck((fileperms($component)&0777)===0600,
            'unsealed backup permissions are not private');
    }

    // Prove the transport survives a real MySQL+private-image restoration,
    // not merely authenticated decryption. Never writes the source database.
    $lease=CmsWriteQuiescence::snapshot($public);
    $restored=CmsSandboxRecovery::replay(
        $cfg,$open['manifest'],$fullDbKey,$public,$sandbox,
        $root.'/database/migrations/001_website_cms.sql',$lease
    );
    $targetDb=Database::connect([...$cfg,'dbname'=>$restored['database']]);
    $image=CmsMediaStore::privatePreview(
        $targetDb,$asset,$restored['media_directory'],$public
    );
    offsiteCheck($image['body']===$picture &&
        (int)$targetDb->query('SELECT COUNT(*) FROM media_assets')->fetchColumn()===1,
        'unsealed encrypted transport could not restore real DB/media');
    CmsSandboxRecovery::cleanup($cfg,$public,$sandbox,$lease);
    $restored=null;$lease->release();
    offsiteCheck(scandir($sandbox)===['.','..'],'SQL recovery left unclean sandbox');
    echo "Stage10: offsite separate-key authenticated ciphertext, tamper/truncate/symlink protection, full real MySQL+media restore — PASS\n";
} finally {
    if ($lease instanceof CmsWriteQuiescence) $lease->release();
    // The CI-only cleanup is performed even after a failed restored MySQL
    // inspection, never against any non-disposable database.
    $lease=CmsWriteQuiescence::snapshot($public);
    try { CmsSandboxRecovery::cleanup($cfg,$public,$sandbox,$lease); }
    finally { $lease->release(); }
    if ($asset!==null) {
        $pdo->prepare('DELETE FROM media_assets WHERE id=?')->execute([$asset]);
    }
    foreach (['CELIKOM_SITE_OFFSITE_KEY','CELIKOM_SITE_WRITE_GATE_FILE'] as $variable) {
        putenv($variable);
    }
    @unlink($base.'/.celikom-cms-writes.lock');
    foreach ([$bundle,$media,$transport] as $directory) {
        foreach (glob($directory.'/*')?:[] as $file) {
            if (is_file($file)||is_link($file)) unlink($file);
        }
        rmdir($directory);
    }
    foreach (glob($recovered.'/*')?:[] as $directory) {
        if (!is_dir($directory)) continue;
        foreach (glob($directory.'/*')?:[] as $file) {
            if (is_file($file)) unlink($file);
        }
        rmdir($directory);
    }
    rmdir($recovered);rmdir($sandbox);rmdir($base);
}
