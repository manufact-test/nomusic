<?php
declare(strict_types=1);
/** Stage 10: REAL MySQL v1 -> v2 + private-media generation switch (CI ONLY). */
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsConfig;
use Celikom\Website\CmsConsistentBackup;
use Celikom\Website\CmsSandboxRecovery;
use Celikom\Website\CmsSandboxGeneration;
use Celikom\Website\CmsMediaStore;
use Celikom\Website\CmsRevisions;
use Celikom\Website\CmsWriteQuiescence;
use Celikom\Website\Database;

function genAssert(bool $ok,string $why):void {
    if (!$ok) throw new RuntimeException('CI versioned generation: '.$why);
}
function genReject(callable $operation,string $why):void {
    try {$operation();} catch (\Throwable $expected) {return;}
    throw new RuntimeException('Generation safety invariant bypassed: '.$why);
}
$config=CmsConfig::databaseSettings();
if (getenv('CI')!=='true' || getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
    $config['dbname']!=='celikom_site_test' || $config['host']!=='127.0.0.1') {
    throw new RuntimeException('Versioned migration is restricted to disposable MySQL CI');
}
$root=dirname(__DIR__);
$public=$root.'/public';
$db=Database::connect($config);
$temp=sys_get_temp_dir().'/celikom-ci-gen-'.bin2hex(random_bytes(10));
$bundle=$temp.'/bundle';$media=$temp.'/media';
$recovery=$temp.'/recovery';$generations=$temp.'/generations';
foreach ([$temp,$bundle,$media,$recovery,$generations] as $path) {
    if (!mkdir($path,0700)) throw new RuntimeException('Cannot allocate private CI fixture');
}
$png=base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true);
genAssert(is_string($png) && strlen($png)>30,'test media corrupted');
$filename=bin2hex(random_bytes(20)).'.png';
file_put_contents($media.'/'.$filename,$png);
chmod($media.'/'.$filename,0600);
putenv('CELIKOM_SITE_WRITE_GATE_FILE='.$temp.'/.celikom-cms-writes.lock');
$key=random_bytes(32);
putenv('CELIKOM_SITE_FULL_BACKUP_KEY='.base64_encode($key));
$fixtureId=null;$lease=null;$restored=null;$generation=null;
$sql=$root.'/tests/fixtures/002_ci_generation_only.sql';
$baseMigration=$root.'/database/migrations/001_website_cms.sql';
$manifest=null;
$baselineSql=(int)$db->query('SELECT COUNT(*) FROM content_revisions')->fetchColumn();
$baselineAudit=(int)$db->query('SELECT COUNT(*) FROM audit_log')->fetchColumn();

try {
    $db->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,'.
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)')
        ->execute(['site-private/'.$filename,'migration-fixture.png','image/png',
            hash('sha256',$png),1,1,'Offline test image',1]);
    $fixtureId=(int)$db->lastInsertId();
    genAssert($fixtureId>0,'source media fixture not stored');
    $lease=CmsWriteQuiescence::snapshot($public);
    $point=CmsConsistentBackup::capture($db,$bundle,$media,$public,$key,$lease);
    $manifest=$point['manifest'];
    $old=CmsSandboxGeneration::seed($config,$generations,$public,$media,$lease);
    genAssert($old['healthy']===true && $old['schema_version']===1 &&
        $old['media_files']===1,'baseline not verified');
    $before=CmsSandboxGeneration::active($config,$generations,$public,$lease);
    genAssert($before['record']['generation']==='gen-baseline','initial pointer mismatch');

    $restored=CmsSandboxRecovery::replay(
        $config,$manifest,$key,$public,$recovery,$baseMigration,$lease
    );
    genAssert($restored['isolated'] && $restored['media_files']===1,'replay invalid');

    genReject(fn()=>CmsSandboxGeneration::migrateAndStage(
        $config,$generations,$public,$restored,$baseMigration,$lease),
        'migration accepts arbitrary SQL path');
    genReject(fn()=>CmsSandboxGeneration::migrateAndStage(
        [...$config,'dbname'=>'celikom'],$generations,$public,$restored,$sql,$lease),
        'migration accepts application DB');
    genAssert(CmsSandboxGeneration::active(
        $config,$generations,$public,$lease
    )['record']===$before['record'],'rejected migration changed active pointer');

    // First DDL persists in MySQL; failed schema migration must leave the
    // unchanged v1 pointer and require discarding the entire v2 SQL generation.
    $fail=static function(string $step):void {
        if ($step==='migration-step-1') {
            throw new RuntimeException('CI interrupted real MySQL DDL');
        }
    };
    genReject(fn()=>CmsSandboxGeneration::migrateAndStage(
        $config,$generations,$public,$restored,$sql,$lease,$fail),
        'injected half-applied MySQL migration');
    genAssert(CmsSandboxGeneration::active(
        $config,$generations,$public,$lease
    )['record']['database']==='celikom_site_test','half migration selected candidate');
    $altered=Database::connect([...$config,'dbname'=>$restored['database']]);
    genAssert((int)$altered->query("SELECT COUNT(*) FROM information_schema.TABLES ".
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='cms_schema_versions'")->fetchColumn()===1,
        'test did not reach committed MySQL DDL');
    genReject(fn()=>CmsSandboxGeneration::migrateAndStage(
        $config,$generations,$public,$restored,$sql,$lease),
        'half-applied migration was retried in place');

    CmsSandboxRecovery::cleanup($config,$public,$recovery,$lease);
    unset($altered);
    $restored=CmsSandboxRecovery::replay(
        $config,$manifest,$key,$public,$recovery,$baseMigration,$lease
    );

    // A separate PHP worker is killed after ALTER TABLE has committed.
    // MySQL DDL is non-transactional: never reuse this partially upgraded DB.
    $lease->release();
    $migrationWorker=<<<'PHP'
require $argv[1];
$cfg=\\Celikom\\Website\\CmsConfig::databaseSettings();
$gate=\\Celikom\\Website\\CmsWriteQuiescence::snapshot($argv[3]);
\\Celikom\\Website\\CmsSandboxGeneration::migrateAndStage(
    $cfg,$argv[2],$argv[3],
    ['database'=>$argv[4],'media_directory'=>$argv[5],'isolated'=>true],
    $argv[6],$gate,
    static function(string $step):void {
        if ($step==='migration-step-2') {
            echo "DDL_COMMITTED\\n";
            fflush(STDOUT);
            sleep(20);
        }
    }
);
PHP;
    $crashed=proc_open([PHP_BINARY,'-r',$migrationWorker,
        $root.'/app/bootstrap.php',$generations,$public,
        $restored['database'],$restored['media_directory'],$sql],
        [1=>['pipe','w'],2=>['pipe','w']],$migrationPipes);
    genAssert(is_resource($crashed),'migration crash worker unavailable');
    stream_set_timeout($migrationPipes[1],9);
    genAssert(fgets($migrationPipes[1])==="DDL_COMMITTED\\n",
        'real ALTER TABLE was not reached before SIGKILL');
    proc_terminate($crashed,9);
    fclose($migrationPipes[1]);fclose($migrationPipes[2]);proc_close($crashed);
    $lease=CmsWriteQuiescence::snapshot($public);
    genAssert(CmsSandboxGeneration::active($config,$generations,$public,$lease)
        ['record']['generation']==='gen-baseline',
        'crashed migration accidentally published version 2');
    $orphan='gen-'.substr($restored['database'],strlen('celikom_site_ci_replay_'));
    CmsSandboxGeneration::discard($config,$generations,$public,$orphan,$lease);
    CmsSandboxRecovery::cleanup($config,$public,$recovery,$lease);
    $restored=CmsSandboxRecovery::replay(
        $config,$manifest,$key,$public,$recovery,$baseMigration,$lease
    );
    $candidate=CmsSandboxGeneration::migrateAndStage(
        $config,$generations,$public,$restored,$sql,$lease
    );
    $generation=$candidate['generation'];
    genAssert($candidate['health']['schema_version']===2 &&
        $candidate['health']['media_files']===1 &&
        $candidate['database']===$restored['database'],
        'version 2 MySQL migration or private media failed');

    $updated=Database::connect([...$config,'dbname'=>$restored['database']]);
    genAssert((int)$updated->query('SELECT COUNT(*) FROM cms_schema_versions WHERE version=2')
        ->fetchColumn()===1 &&
        (int)$updated->query('SELECT COUNT(*) FROM site_settings')->fetchColumn()===
        (int)$db->query('SELECT COUNT(*) FROM site_settings')->fetchColumn(),
        'versioned migration lost settings or version record');
    $v10=file_get_contents($root.'/app/Templates/site-v10.html');
    $fields=file_get_contents($root.'/app/Config/content-fields-v10.json');
    $faq=file_get_contents($root.'/database/seeds/faq-v10.json');
    genAssert(is_string($v10) && is_string($fields) && is_string($faq) &&
        CmsRevisions::publishedPage($updated,$v10,$fields,$faq)===
        CmsRevisions::publishedPage($db,$v10,$fields,$faq),
        'real restored MySQL renders different approved v10');

    $halt=static function(string $step):void {
        if ($step==='before-switch') throw new RuntimeException('CI crash before pointer rename');
    };
    genReject(fn()=>CmsSandboxGeneration::select(
        $config,$generations,$public,$generation,$lease,$halt),
        'injected pre-rename failure');
    genAssert(CmsSandboxGeneration::active(
        $config,$generations,$public,$lease
    )['record']['generation']==='gen-baseline',
        'pre-rename error changed active release');

    // Tamper a staged image: no pointer switch is permitted before actual
    // MySQL+media integrity check passes.
    $stagedPath=$generations.'/'.$generation.'/media/'.$filename;
    $saved=(string)file_get_contents($stagedPath);
    file_put_contents($stagedPath,'tampered image');
    genReject(fn()=>CmsSandboxGeneration::select(
        $config,$generations,$public,$generation,$lease),
        'damaged private image passed release health');
    file_put_contents($stagedPath,$saved);
    chmod($stagedPath,0600);

    $switch=CmsSandboxGeneration::select(
        $config,$generations,$public,$generation,$lease
    );
    genAssert($switch['active']['schema_version']===2 &&
        CmsSandboxGeneration::active(
            $config,$generations,$public,$lease
        )['record']['database']===$restored['database'],
        'atomic version-2 pointer activation failed');
    genReject(fn()=>CmsSandboxGeneration::discard(
        $config,$generations,$public,$generation,$lease),
        'active generation deleted');

    // Backward-compatible read-only health checks permit rollback by
    // selecting the preserved v1 generation; NO down-migration of SQL.
    CmsSandboxGeneration::select($config,$generations,$public,'gen-baseline',$lease);
    genAssert(CmsSandboxGeneration::active(
        $config,$generations,$public,$lease
    )['health']['schema_version']===1,'rollback cannot read old MySQL');

    // A tampered pointer may not select an arbitrary database.
    $pointer=$generations.'/.celikom-ci-active-generation.json';
    $original=(string)file_get_contents($pointer);
    $fake=json_decode($original,true,16,JSON_THROW_ON_ERROR);
    $fake['database']='celikom';
    file_put_contents($pointer,json_encode($fake,JSON_THROW_ON_ERROR));
    genReject(fn()=>CmsSandboxGeneration::active(
        $config,$generations,$public,$lease),'tampered active pointer');
    file_put_contents($pointer,$original);
    chmod($pointer,0600);
    $lease->release();

    // Different PHP worker performs pointer rename then gets SIGKILL before
    // returning. A new worker must read EITHER committed valid v2 or old v1
    // and be able to select the old version without touching SQL.
    $child=<<<'PHP'
require $argv[1];
$cfg=\Celikom\Website\CmsConfig::databaseSettings();
$gate=\Celikom\Website\CmsWriteQuiescence::snapshot($argv[3]);
\Celikom\Website\CmsSandboxGeneration::select(
    $cfg,$argv[2],$argv[3],$argv[4],$gate,
    static function(string $step):void {
        if ($step==='after-switch') {
            echo "SWITCHED\n";
            fflush(STDOUT);
            sleep(20);
        }
    }
);
PHP;
    $process=proc_open([PHP_BINARY,'-r',$child,
        $root.'/app/bootstrap.php',$generations,$public,$generation],
        [1=>['pipe','w'],2=>['pipe','w']],$pipes);
    genAssert(is_resource($process),'could not start selector worker');
    stream_set_timeout($pipes[1],9);
    genAssert(fgets($pipes[1])==="SWITCHED\n",
        'selector worker did not commit pointer before crash');
    proc_terminate($process,9);
    fclose($pipes[1]);fclose($pipes[2]);proc_close($process);
    $lease=CmsWriteQuiescence::snapshot($public);
    $active=CmsSandboxGeneration::active($config,$generations,$public,$lease);
    genAssert($active['record']['generation']===$generation &&
        $active['health']['healthy']===true,'crashed selector left broken release');
    CmsSandboxGeneration::select($config,$generations,$public,'gen-baseline',$lease);
    CmsSandboxGeneration::discard($config,$generations,$public,$generation,$lease);
    $generation=null;
    CmsSandboxRecovery::cleanup($config,$public,$recovery,$lease);
    $restored=null;
    genAssert((int)$db->query('SELECT COUNT(*) FROM content_revisions')->fetchColumn()===
        $baselineSql && (int)$db->query('SELECT COUNT(*) FROM audit_log')->fetchColumn()===
        $baselineAudit,'source SQL mutated by migration or release');
    genAssert(!is_file($root.'/RELEASE_READY') &&
        !is_file($public.'/media/'.$filename),
        'offline release accidentally authorized or published media');
    echo "Stage10: isolated SQL v1->v2, private media versions, damaged candidate rejection, atomic switch, rollback and SIGKILL recovery — PASS\n";
} finally {
    if ($lease instanceof CmsWriteQuiescence) $lease->release();
    $lease=CmsWriteQuiescence::snapshot($public);
    try {
        if (is_string($generation)) {
            $selection=CmsSandboxGeneration::active($config,$generations,$public,$lease);
            if ($selection['record']['generation']===$generation) {
                CmsSandboxGeneration::select(
                    $config,$generations,$public,'gen-baseline',$lease
                );
            }
            CmsSandboxGeneration::discard(
                $config,$generations,$public,$generation,$lease
            );
        }
        CmsSandboxRecovery::cleanup($config,$public,$recovery,$lease);
    } finally { $lease->release(); }
    if ($fixtureId!==null) {
        $db->prepare('DELETE FROM media_assets WHERE id=?')->execute([$fixtureId]);
    }
    putenv('CELIKOM_SITE_FULL_BACKUP_KEY');
    putenv('CELIKOM_SITE_WRITE_GATE_FILE');
    @unlink($temp.'/.celikom-cms-writes.lock');
    foreach ([$bundle,$media] as $dir) {
        foreach (glob($dir.'/*')?:[] as $item) {
            if (is_file($item)) unlink($item);
        }
        rmdir($dir);
    }
    @unlink($generations.'/.celikom-ci-active-generation.json');
    $baselineFolder=$generations.'/gen-baseline';
    foreach (glob($baselineFolder.'/media/*')?:[] as $item) {
        if (is_file($item)) unlink($item);
    }
    if (is_dir($baselineFolder.'/media')) rmdir($baselineFolder.'/media');
    @unlink($baselineFolder.'/.generation.json');
    if (is_dir($baselineFolder)) rmdir($baselineFolder);
    rmdir($generations);
    rmdir($recovery);
    rmdir($temp);
}
