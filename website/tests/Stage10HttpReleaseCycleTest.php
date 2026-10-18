<?php
declare(strict_types=1);
/** Stage 10 CI-only real HTTP, journaled generation cutover and rollback. */
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsConfig;
use Celikom\Website\CmsConsistentBackup;
use Celikom\Website\CmsSandboxGeneration;
use Celikom\Website\CmsSandboxRecovery;
use Celikom\Website\CmsSandboxReleaseCycle;
use Celikom\Website\CmsWriteQuiescence;
use Celikom\Website\Database;

function httpCycleAssert(bool $value,string $why):void {
    if (!$value) throw new RuntimeException('CI HTTP generation cycle: '.$why);
}
function httpCycleReject(callable $operation,string $why):void {
    try {$operation();} catch (\Throwable $error) {return;}
    throw new RuntimeException('HTTP release cycle accepted unsafe state: '.$why);
}
function httpCycleRequest(int $port,string $path,string $method='GET',?string $host=null):array {
    $context=stream_context_create(['http'=>[
        'method'=>$method,'ignore_errors'=>true,'timeout'=>5,
        'header'=>'Host: '.($host??('127.0.0.1:'.$port))."\r\n".
            'Connection: close'."\r\n",
    ]]);
    $body=@file_get_contents('http://127.0.0.1:'.$port.$path,false,$context);
    $headers=$http_response_header??[];
    $status=0;
    if (isset($headers[0]) && preg_match('~^HTTP/1\\.[01] ([0-9]{3})~',$headers[0],$m)) {
        $status=(int)$m[1];
    }
    return ['status'=>$status,'body'=>is_string($body)?$body:'',
        'headers'=>implode("\n",$headers)];
}
function httpCycleRead(int $port,string $generation,int $version,?string $expectedHash=null):string {
    $check=httpCycleRequest($port,'/__ci/health');
    httpCycleAssert($check['status']===200,'unhealthy loopback generation: '.$check['status']);
    $data=json_decode($check['body'],true,32,JSON_THROW_ON_ERROR);
    httpCycleAssert(($data['healthy']??null)===true &&
        $data['generation']===$generation &&
        $data['schema_version']===$version &&
        $data['media_files']===1 &&
        preg_match('/^[a-f0-9]{64}$/D',$data['html_sha256'])===1,
        'generation, schema, media or HTML digest mismatch');
    $page=httpCycleRequest($port,'/__ci/page');
    httpCycleAssert($page['status']===200 && strlen($page['body'])>5000 &&
        hash('sha256',$page['body'])===$data['html_sha256'] &&
        stripos($page['headers'],'X-Robots-Tag: noindex')!==false,
        'MySQL v10 HTTP page and health digest differ or lack noindex');
    if ($expectedHash!==null) {
        httpCycleAssert($data['html_sha256']===$expectedHash,
            'approved v10 changes during SQL generation switch');
    }
    return $data['html_sha256'];
}

$config=CmsConfig::databaseSettings();
if (getenv('CI')!=='true' ||
    getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
    $config['host']!=='127.0.0.1' ||
    $config['dbname']!=='celikom_site_test') {
    throw new RuntimeException('HTTP release rehearsal restricted to disposable CI MySQL');
}
$site=dirname(__DIR__);$public=$site.'/public';
$temp=sys_get_temp_dir().'/celikom-http-cycle-'.bin2hex(random_bytes(10));
$bundle=$temp.'/bundle';$media=$temp.'/media';
$recovery=$temp.'/recovery';$generations=$temp.'/generations';
foreach ([$temp,$bundle,$media,$recovery,$generations] as $dir) {
    if (!mkdir($dir,0700)) throw new RuntimeException('Cannot allocate isolated HTTP fixture');
}
$pdo=Database::connect($config);
$key=random_bytes(32);
$filename=bin2hex(random_bytes(20)).'.png';
$bytes=base64_decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true
);
httpCycleAssert(is_string($bytes) && strlen($bytes)>30,'synthetic binary PNG missing');
file_put_contents($media.'/'.$filename,$bytes);
chmod($media.'/'.$filename,0600);
putenv('CELIKOM_SITE_WRITE_GATE_FILE='.$temp.'/.celikom-cms-writes.lock');
putenv('CELIKOM_SITE_FULL_BACKUP_KEY='.base64_encode($key));
putenv('CELIKOM_SITE_HTTP_SANDBOX=1');
putenv('CELIKOM_SITE_CI_GENERATION_ROOT='.$generations);
$lease=null;$assetId=null;$server=null;$candidate=null;$restored=null;$port=0;
$journal=$generations.'/.celikom-ci-release-cycle.json';
$originalAudit=(int)$pdo->query('SELECT COUNT(*) FROM audit_log')->fetchColumn();

try {
    $pdo->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,'.
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)')
        ->execute(['site-private/'.$filename,'http-test.png','image/png',
            hash('sha256',$bytes),1,1,'CI offline image only',1]);
    $assetId=(int)$pdo->lastInsertId();
    httpCycleAssert($assetId>0,'failed to create media fixture');

    $lease=CmsWriteQuiescence::snapshot($public);
    $capture=CmsConsistentBackup::capture($pdo,$bundle,$media,$public,$key,$lease);
    CmsSandboxGeneration::seed($config,$generations,$public,$media,$lease);
    $restored=CmsSandboxRecovery::replay(
        $config,$capture['manifest'],$key,$public,$recovery,
        $site.'/database/migrations/001_website_cms.sql',$lease
    );
    $staged=CmsSandboxGeneration::migrateAndStage(
        $config,$generations,$public,$restored,
        $site.'/tests/fixtures/002_ci_generation_only.sql',$lease
    );
    $candidate=$staged['generation'];
    httpCycleAssert($staged['health']['healthy']===true,'real v2 SQL/media candidate unhealthy');
    $lease->release();

    $listener=stream_socket_server('tcp://127.0.0.1:0',$errno,$reason);
    httpCycleAssert(is_resource($listener),'cannot allocate loopback HTTP port');
    $addr=(string)stream_socket_get_name($listener,false);
    $port=(int)substr(strrchr($addr,':'),1);
    fclose($listener);
    httpCycleAssert($port>1024,'invalid CI ephemeral HTTP port');
    $server=proc_open([PHP_BINARY,'-S','127.0.0.1:'.$port,'-t',$public,
        $site.'/tests/fixtures/offline-generation-router.php'],
        [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
    httpCycleAssert(is_resource($server),'cannot start local CI HTTP server');
    fclose($pipes[0]);
    $ready=false;
    for ($attempt=0;$attempt<40;$attempt++) {
        usleep(100000);
        if (httpCycleRequest($port,'/__ci/health')['status']===200) {
            $ready=true;break;
        }
    }
    httpCycleAssert($ready,'CI router did not expose healthy baseline');

    $front=httpCycleRequest($port,'/');
    $admin=httpCycleRequest($port,'/admin/');
    httpCycleAssert($front['status']===503 && $admin['status']===503 &&
        stripos($front['headers'],'X-Robots-Tag: noindex')!==false &&
        stripos($admin['headers'],'X-Robots-Tag: noindex')!==false,
        'original public / or /admin/ was accidentally activated');
    httpCycleAssert(httpCycleRequest($port,'/__ci/health','POST')['status']===405 &&
        httpCycleRequest($port,'/__ci/unknown')['status']===404 &&
        httpCycleRequest($port,'/__ci/health','GET','other-host.invalid')['status']===503,
        'sandbox HTTP endpoints accepted writes, unknown routes or wrong host');
    $hash=httpCycleRead($port,'gen-baseline',1);

    // HTTP health requires the same exclusive lease as the selector. It must
    // fail closed while a separate writer/snapshot owns that lease.
    $lease=CmsWriteQuiescence::snapshot($public);
    httpCycleAssert(httpCycleRequest($port,'/__ci/health')['status']===503,
        'HTTP probe bypassed exclusive lock held by another PHP process');

    CmsSandboxReleaseCycle::prepare(
        $config,$generations,$public,$candidate,$lease
    );
    httpCycleReject(fn()=>CmsSandboxReleaseCycle::prepare(
        $config,$generations,$public,$candidate,$lease),
        'two overlapping release journals');
    httpCycleReject(fn()=>CmsSandboxReleaseCycle::activate(
        $config,$generations,$public,$lease,
        static function(string $stage):void {
            if ($stage==='before-pointer-rename') {
                throw new RuntimeException('Injected early release failure');
            }
        }),
        'fault before selector rename');
    httpCycleAssert(CmsSandboxGeneration::currentRecord(
        $config,$generations,$public,$lease
    )['generation']==='gen-baseline','early exception changed active pointer');
    CmsSandboxReleaseCycle::reconcile($config,$generations,$public,$lease);
    httpCycleAssert(!file_exists($journal),'prepared release journal not reconciled');
    $lease->release();
    httpCycleRead($port,'gen-baseline',1,$hash);

    $lease=CmsWriteQuiescence::snapshot($public);
    CmsSandboxReleaseCycle::prepare($config,$generations,$public,$candidate,$lease);
    httpCycleReject(fn()=>CmsSandboxReleaseCycle::activate(
        $config,$generations,$public,$lease,
        static function(string $stage):void {
            if ($stage==='after-pointer-rename') {
                throw new RuntimeException('Crash between pointer and journal phase');
            }
        }),
        'fault after atomic rename');
    $lease->release();
    httpCycleRead($port,$candidate,2,$hash);

    // Candidate is now active but media breaks before a recovery worker runs.
    // Unhealthy HTTP must not serve a partial page, and rollback must still
    // work without first requiring damaged v2 health.
    $candidateMedia=$generations.'/'.$candidate.'/media/'.$filename;
    $saved=(string)file_get_contents($candidateMedia);
    file_put_contents($candidateMedia,'bad image');
    httpCycleAssert(httpCycleRequest($port,'/__ci/health')['status']===503,
        'corrupt active binary media was served via HTTP');
    $lease=CmsWriteQuiescence::snapshot($public);
    CmsSandboxReleaseCycle::reconcile($config,$generations,$public,$lease);
    $lease->release();
    httpCycleRead($port,'gen-baseline',1,$hash);
    file_put_contents($candidateMedia,$saved);
    chmod($candidateMedia,0600);

    // A healthy acknowledged release can be confirmed; a confirmed pointer
    // stays current if the intent file is removed. Rollback still uses v1.
    $lease=CmsWriteQuiescence::snapshot($public);
    CmsSandboxReleaseCycle::prepare($config,$generations,$public,$candidate,$lease);
    CmsSandboxReleaseCycle::activate($config,$generations,$public,$lease);
    CmsSandboxReleaseCycle::confirm($config,$generations,$public,$lease);
    httpCycleAssert(!file_exists($journal),'confirmed release journal persisted');
    $lease->release();
    httpCycleRead($port,$candidate,2,$hash);
    $lease=CmsWriteQuiescence::snapshot($public);
    CmsSandboxGeneration::select($config,$generations,$public,'gen-baseline',$lease);
    $lease->release();
    httpCycleRead($port,'gen-baseline',1,$hash);

    // A separate worker is SIGKILLed AFTER pointer rename, BEFORE journal
    // promotion. The next owner replays the journal, not a SQL down-migration.
    $lease=CmsWriteQuiescence::snapshot($public);
    CmsSandboxReleaseCycle::prepare($config,$generations,$public,$candidate,$lease);
    $lease->release();
    $child=<<<'PHP'
require $argv[1];
$cfg=\Celikom\Website\CmsConfig::databaseSettings();
$lock=\Celikom\Website\CmsWriteQuiescence::snapshot($argv[3]);
\Celikom\Website\CmsSandboxReleaseCycle::activate(
    $cfg,$argv[2],$argv[3],$lock,
    static function(string $stage):void {
        if ($stage==='after-pointer-rename') {
            echo "SWITCHED\n";
            fflush(STDOUT);
            sleep(20);
        }
    }
);
PHP;
    $worker=proc_open([PHP_BINARY,'-r',$child,
        $site.'/app/bootstrap.php',$generations,$public],
        [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$wpipes);
    httpCycleAssert(is_resource($worker),'crash worker failed to launch');
    fclose($wpipes[0]);
    stream_set_timeout($wpipes[1],10);
    httpCycleAssert(fgets($wpipes[1])==="SWITCHED\n",
        'independent worker never committed release pointer');
    proc_terminate($worker,9);
    fclose($wpipes[1]);fclose($wpipes[2]);proc_close($worker);
    httpCycleRead($port,$candidate,2,$hash);
    $lease=CmsWriteQuiescence::snapshot($public);
    CmsSandboxReleaseCycle::reconcile($config,$generations,$public,$lease);
    $lease->release();
    httpCycleRead($port,'gen-baseline',1,$hash);

    httpCycleAssert((int)$pdo->query('SELECT COUNT(*) FROM audit_log')->fetchColumn()===
        $originalAudit && is_file($media.'/'.$filename) &&
        !file_exists($site.'/RELEASE_READY'),
        'source CMS or production release gate changed during HTTP rehearsals');
    echo "Stage10: real loopback HTTP SQL v1/v2 page hashes, protected live 503, release journal, corruption rollback and SIGKILL recovery — PASS\n";
} finally {
    if ($lease instanceof CmsWriteQuiescence) $lease->release();
    if (is_resource($server)) {
        proc_terminate($server,9);
        foreach ([1,2] as $i) {
            if (isset($pipes[$i]) && is_resource($pipes[$i])) fclose($pipes[$i]);
        }
        proc_close($server);
    }
    $lease=CmsWriteQuiescence::snapshot($public);
    try {
        if (file_exists($journal)) {
            CmsSandboxReleaseCycle::reconcile($config,$generations,$public,$lease);
        }
        if (is_string($candidate)) {
            $current=CmsSandboxGeneration::currentRecord(
                $config,$generations,$public,$lease
            );
            if ($current['generation']===$candidate) {
                CmsSandboxGeneration::select(
                    $config,$generations,$public,'gen-baseline',$lease
                );
            }
            CmsSandboxGeneration::discard(
                $config,$generations,$public,$candidate,$lease
            );
        }
        CmsSandboxRecovery::cleanup($config,$public,$recovery,$lease);
    } finally {
        $lease->release();
    }
    if ($assetId!==null) {
        $pdo->prepare('DELETE FROM media_assets WHERE id=?')->execute([$assetId]);
    }
    foreach (['CELIKOM_SITE_HTTP_SANDBOX','CELIKOM_SITE_CI_GENERATION_ROOT',
        'CELIKOM_SITE_FULL_BACKUP_KEY','CELIKOM_SITE_WRITE_GATE_FILE'] as $variable) {
        putenv($variable);
    }
    @unlink($temp.'/.celikom-cms-writes.lock');
    foreach ([$bundle,$media] as $dir) {
        foreach (glob($dir.'/*')?:[] as $item) {
            if (is_file($item)) unlink($item);
        }
        rmdir($dir);
    }
    @unlink($generations.'/.celikom-ci-active-generation.json');
    $old=$generations.'/gen-baseline';
    foreach (glob($old.'/media/*')?:[] as $file) {
        if (is_file($file)) unlink($file);
    }
    if (is_dir($old.'/media')) rmdir($old.'/media');
    @unlink($old.'/.generation.json');
    if (is_dir($old)) rmdir($old);
    rmdir($generations);
    rmdir($recovery);
    rmdir($temp);
}
