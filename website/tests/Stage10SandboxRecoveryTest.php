<?php
declare(strict_types=1);
/** Stage 10: durable real MySQL+private-media restore in disposable CI ONLY. */
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsConfig;
use Celikom\Website\CmsConsistentBackup;
use Celikom\Website\CmsSandboxRecovery;
use Celikom\Website\CmsMediaStore;
use Celikom\Website\CmsWriteQuiescence;
use Celikom\Website\Database;

function replayAssert(bool $ok,string $reason):void {
    if (!$ok) throw new RuntimeException('CI MySQL recovery: '.$reason);
}
function replayReject(callable $test,string $reason):void {
    try { $test(); } catch (\Throwable $e) {return;}
    throw new RuntimeException('Unsafe MySQL recovery accepted: '.$reason);
}
$config=CmsConfig::databaseSettings();
if (getenv('CI')!=='true' ||
    getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
    $config['host']!=='127.0.0.1' ||
    $config['dbname']!=='celikom_site_test') {
    throw new RuntimeException('Stage10 MySQL recovery strictly requires disposable CI');
}
$base=dirname(__DIR__);
$pdo=Database::connect($config);
$temp=sys_get_temp_dir().'/celikom-sql-replay-'.bin2hex(random_bytes(10));
$bundle=$temp.'/bundle';
$media=$temp.'/media';
$sandbox=$temp.'/sandbox';
foreach ([$temp,$bundle,$media,$sandbox] as $path) {
    if (!mkdir($path,0700)) throw new RuntimeException('Cannot make isolated test root');
}
putenv('CELIKOM_SITE_WRITE_GATE_FILE='.$temp.'/.celikom-cms-writes.lock');
$key=random_bytes(32);
putenv('CELIKOM_SITE_FULL_BACKUP_KEY='.base64_encode($key));
$filename=bin2hex(random_bytes(20)).'.png';
$fixture=base64_decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true
);
replayAssert(is_string($fixture) && strlen($fixture)>30,'private synthetic image invalid');
$assetId=null;
$gate=null;
$manifest=null;
$originalRowCount=(int)$pdo->query('SELECT COUNT(*) FROM audit_log')->fetchColumn();
$migration=$base.'/database/migrations/001_website_cms.sql';
$public=$base.'/public';
$replay=static function(?callable $fault=null) use (
    $config,&$manifest,$key,$public,$sandbox,$migration
):array {
    $lock=CmsWriteQuiescence::snapshot($public);
    try {
        return CmsSandboxRecovery::replay(
            $config,$manifest,$key,$public,$sandbox,$migration,$lock,$fault
        );
    } finally {
        $lock->release();
    }
};
try {
    file_put_contents($media.'/'.$filename,$fixture);
    chmod($media.'/'.$filename,0600);
    $pdo->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,'.
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)')
        ->execute(['site-private/'.$filename,'ci-only-replay.png','image/png',
            hash('sha256',$fixture),1,1,'CI replay only',1]);
    $assetId=(int)$pdo->lastInsertId();
    replayAssert($assetId>0,'could not create source image row');
    $gate=CmsWriteQuiescence::snapshot($public);
    $snapshot=CmsConsistentBackup::capture($pdo,$bundle,$media,$public,$key,$gate);
    $manifest=$snapshot['manifest'];
    $gate->release();

    // NO write target may be touched if input, key, migration or CI guard fails.
    $lease=CmsWriteQuiescence::snapshot($public);
    replayReject(fn()=>CmsSandboxRecovery::replay($config,$manifest,
        random_bytes(32),$public,$sandbox,$migration,$lease),
        'wrong backup key');
    replayReject(fn()=>CmsSandboxRecovery::replay($config,$manifest,$key,
        $public,$public,$migration,$lease),'recovery inside public root');
    file_put_contents($temp.'/altered-schema.sql','CREATE TABLE test_bad (id INT);');
    replayReject(fn()=>CmsSandboxRecovery::replay($config,$manifest,$key,
        $public,$sandbox,$temp.'/altered-schema.sql',$lease),
        'unexpected target schema');
    putenv('CI=false');
    replayReject(fn()=>CmsSandboxRecovery::replay($config,$manifest,$key,
        $public,$sandbox,$migration,$lease),'outside CI');
    putenv('CI=true');
    $lease->release();
    replayAssert(scandir($sandbox)===['.','..'],'invalid input mutated target');

    // Each exception during real DDL/SQL/media replay must drop ONLY the new
    // isolated DB and staged files. The original CMS never changes.
    foreach ([
        'journal-created','media-staged','database-created','schema-checked',
        'first-row-inserted','rows-committed','verified'
    ] as $point) {
        $fault=static function(string $step) use ($point):void {
            if ($step===$point) throw new RuntimeException('CI injected '.$point);
        };
        replayReject(fn()=>$replay($fault),'injected failure at '.$point);
        replayAssert(scandir($sandbox)===['.','..'] &&
            (int)$pdo->query("SELECT COUNT(*) FROM information_schema.SCHEMATA ".
                "WHERE SCHEMA_NAME LIKE 'celikom_site_ci_replay_%'")->fetchColumn()===0,
            'partial SQL/media recovery survived '.$point);
    }

    $lease=CmsWriteQuiescence::snapshot($public);
    $restored=CmsSandboxRecovery::replay(
        $config,$manifest,$key,$public,$sandbox,$migration,$lease
    );
    replayAssert($restored['isolated']===true &&
        $restored['media_files']===1 &&
        str_starts_with($restored['database'],'celikom_site_ci_replay_') &&
        is_file($restored['media_directory'].'/'.$filename),
        'valid coordinated restore did not stage media and SQL');
    $new=Database::connect([...$config,'dbname'=>$restored['database']]);
    replayAssert((int)$new->query('SELECT COUNT(*) FROM audit_log')->fetchColumn()===
        $originalRowCount &&
        (int)$new->query('SELECT COUNT(*) FROM media_assets')->fetchColumn()===1,
        'audit/user data or asset rows lost');
    $image=CmsMediaStore::privatePreview(
        $new,$assetId,$restored['media_directory'],$public
    );
    replayAssert($image['body']===$fixture,'media bytes missing after SQL import');

    // Malicious or corrupted journal must fail closed rather than DROP source.
    $journal=$sandbox.'/.celikom-ci-mysql-recovery.json';
    $original=(string)file_get_contents($journal);
    $fake=json_decode($original,true,16,JSON_THROW_ON_ERROR);
    $fake['database']='celikom_site_test';
    file_put_contents($journal,json_encode($fake,JSON_THROW_ON_ERROR));
    replayReject(fn()=>CmsSandboxRecovery::cleanup($config,$public,$sandbox,$lease),
        'journal referencing source database');
    replayAssert((int)$pdo->query('SELECT COUNT(*) FROM media_assets')->fetchColumn()>=1,
        'tampered journal changed original DB');
    file_put_contents($journal,$original);
    CmsSandboxRecovery::cleanup($config,$public,$sandbox,$lease);
    $lease->release();
    replayAssert(scandir($sandbox)===['.','..'],'successful restore cleanup left files');
    unset($new);

    // A DIFFERENT PHP worker is SIGKILLed after real CREATE DATABASE.
    // Its finally/catch cannot run; next owner must clean the persisted journal.
    $child=<<<'PHP'
require $argv[1];
$cfg=\Celikom\Website\CmsConfig::databaseSettings();
$gate=\Celikom\Website\CmsWriteQuiescence::snapshot($argv[3]);
\Celikom\Website\CmsSandboxRecovery::replay(
    $cfg,$argv[2],\Celikom\Website\CmsFullDbBackup::keyFromEnv(),
    $argv[3],$argv[4],$argv[5],$gate,
    static function(string $step):void {
        if ($step==='database-created') {
            echo "CREATED\n";
            fflush(STDOUT);
            sleep(20);
        }
    }
);
PHP;
    $process=proc_open([PHP_BINARY,'-r',$child,
        $base.'/app/bootstrap.php',$manifest,$public,$sandbox,$migration],
        [1=>['pipe','w'],2=>['pipe','w']],$pipes);
    replayAssert(is_resource($process),'could not launch crash worker');
    stream_set_timeout($pipes[1],9);
    $line=fgets($pipes[1]);
    replayAssert($line==="CREATED\n",'crash worker did not create SQL schema');
    proc_terminate($process,9);
    fclose($pipes[1]);
    fclose($pipes[2]);
    proc_close($process);
    replayAssert(is_file($journal),'crashed worker left no recovery journal');
    $lease=CmsWriteQuiescence::snapshot($public);
    CmsSandboxRecovery::cleanup($config,$public,$sandbox,$lease);
    $lease->release();
    replayAssert(scandir($sandbox)===['.','..'] &&
        (int)$pdo->query("SELECT COUNT(*) FROM information_schema.SCHEMATA ".
            "WHERE SCHEMA_NAME LIKE 'celikom_site_ci_replay_%'")->fetchColumn()===0,
        'SIGKILL did not permit journal-led DB+media cleanup');
    replayAssert((int)$pdo->query('SELECT COUNT(*) FROM audit_log')->fetchColumn()===
        $originalRowCount && is_file($media.'/'.$filename),
        'recovery modified source audit/media');
    echo "Stage10: real isolated MySQL rows + binary media replay, faults, tamper, wrong schema, SIGKILL journal recovery — PASS\n";
} finally {
    if ($gate instanceof CmsWriteQuiescence) $gate->release();
    if (isset($lease) && $lease instanceof CmsWriteQuiescence) $lease->release();
    $lease=CmsWriteQuiescence::snapshot($public);
    try {CmsSandboxRecovery::cleanup($config,$public,$sandbox,$lease);}
    finally {$lease->release();}
    if ($assetId!==null) {
        $pdo->prepare('DELETE FROM media_assets WHERE id=?')->execute([$assetId]);
    }
    putenv('CELIKOM_SITE_FULL_BACKUP_KEY');
    putenv('CELIKOM_SITE_WRITE_GATE_FILE');
    @unlink($temp.'/.celikom-cms-writes.lock');
    foreach ([$bundle,$media] as $dir) {
        foreach(glob($dir.'/*')?:[] as $file) {
            if(is_file($file)||is_link($file))unlink($file);
        }
        rmdir($dir);
    }
    @unlink($temp.'/altered-schema.sql');
    rmdir($sandbox);
    rmdir($temp);
}
