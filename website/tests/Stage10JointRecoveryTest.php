<?php
declare(strict_types=1);
/**
 * Large Stage 10 disposable recovery drill: match BOTH independent backups,
 * restore full CMS MySQL tables and private binary media in a brand-new DB
 * and owner-only folder, then compare public rendering / auth / logs.
 *
 * Refuses every non-CI source DB. Does not touch production or Hostinger.
 */
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsBackup;
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsFullDbBackup;
use Celikom\Website\CmsMediaStore;
use Celikom\Website\CmsRecoveryPair;
use Celikom\Website\CmsRevisions;
use Celikom\Website\Database;

function pairedAssert(bool $ok,string $reason):void {
    if(!$ok)throw new RuntimeException('Stage 10 combined recovery: '.$reason);
}
function pairedReject(callable $task,string $reason):void {
    try{$task();} catch(\Throwable $e) {return;}
    throw new RuntimeException('Combined recovery accepted unsafe pair: '.$reason);
}
$cfg=CmsConfig::databaseSettings();
if(getenv('CI')!=='true' || getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
    $cfg['dbname']!=='celikom_site_test' || $cfg['host']!=='127.0.0.1') {
    throw new RuntimeException('Joint restore strictly restricted to isolated CI MySQL');
}
$src=Database::connect($cfg);
$root=dirname(__DIR__);
$temp=sys_get_temp_dir().'/celikom-joint-recovery-'.bin2hex(random_bytes(9));
$fullDir=$temp.'/encrypted';
$contentDir=$temp.'/content';
$privateMedia=$temp.'/source-media';
$restoredMedia=$temp.'/restored-media';
$dirs=[$temp,$fullDir,$contentDir,$privateMedia,$restoredMedia];
foreach($dirs as $dir) {
    if(!mkdir($dir,0700))throw new RuntimeException('Private fixture cannot be created');
}
$newDb='celikom_site_pair_restore_'.bin2hex(random_bytes(5));
$key=random_bytes(32);
$created=false;
$assetId=null;
$keyName=bin2hex(random_bytes(20)).'.png';
$mediaPath=$privateMedia.'/'.$keyName;
$fixture=base64_decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true
);
pairedAssert(is_string($fixture) && strlen($fixture)>30,'synthetic private PNG missing');
try {
    file_put_contents($mediaPath,$fixture);
    chmod($mediaPath,0600);
    $src->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,'.
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)')
        ->execute(['site-private/'.$keyName,'synthetic.png','image/png',
            hash('sha256',$fixture),1,1,'Private test only',1]);
    $assetId=(int)$src->lastInsertId();
    pairedAssert($assetId>0,'source media fixture not inserted');

    // Two independent tools capture the same otherwise-idle CI test DB.
    $full=CmsFullDbBackup::export($src,$fullDir,$root.'/public',$key);
    $content=CmsBackup::export($src,$contentDir,$privateMedia,$root.'/public');
    $report=CmsRecoveryPair::inspect($full,$content,$key,$root.'/public');
    pairedAssert($report['consistent'] &&
        $report['rows']['media_assets']===1 &&
        $report['rows']['content_revisions']>=3 &&
        $report['rows']['site_state']===1 &&
        $report['media_files']===1 &&
        $report['published_id']===CmsRevisions::publishedId($src),
        'complete snapshot parity across both independent backups');
    pairedReject(fn()=>CmsRecoveryPair::inspect($full,$content,random_bytes(32),
        $root.'/public'),'wrong encryption key');
    pairedReject(fn()=>CmsRecoveryPair::inspect($full,$full,$key,
        $root.'/public'),'same file passed as two backups');

    // An attacker can re-hash a plaintext envelope; cross-check still catches
    // a forged content revision that differs from the authenticated full DB.
    $envelope=json_decode((string)file_get_contents($content),true,512,JSON_THROW_ON_ERROR);
    $modified=$envelope;
    $modified['payload']['tables']['content_revisions'][0]['change_note']='forged';
    $canonical=json_encode($modified['payload'],
        JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
    $modified['sha256']=hash('sha256',$canonical);
    $fake=$contentDir.'/forged.json';
    file_put_contents($fake,json_encode($modified,
        JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES));
    chmod($fake,0600);
    pairedReject(fn()=>CmsRecoveryPair::inspect($full,$fake,$key,
        $root.'/public'),'rehashed inconsistent content history');
    $modified=$envelope;
    $modified['payload']['tables']['media_assets'][0]['pixel_width']=2;
    $modified['sha256']=hash('sha256',json_encode($modified['payload'],
        JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES));
    file_put_contents($fake,json_encode($modified,
        JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES));
    pairedReject(fn()=>CmsRecoveryPair::inspect($full,$fake,$key,
        $root.'/public'),'rehashed inconsistent private media metadata');
    unlink($fake);
    chmod($content,0644);
    pairedReject(fn()=>CmsRecoveryPair::inspect($full,$content,$key,
        $root.'/public'),'world-readable private content copy');
    chmod($content,0600);

    // Restore only after verification into a DISTINCT disposable database.
    $src->exec('CREATE DATABASE '.$newDb.' CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');
    $created=true;
    $restored=Database::connect([...$cfg,'dbname'=>$newDb]);
    $sql=preg_replace('/^--.*$/m','',
        (string)file_get_contents($root.'/database/migrations/001_website_cms.sql'));
    foreach(explode(';',$sql) as $statement) {
        if(trim($statement)!=='')$restored->exec(trim($statement));
    }
    $restored->exec('DELETE FROM site_state WHERE id=1');
    $restored->beginTransaction();
    try {
        $counts=[];
        CmsFullDbBackup::inspect($full,$key,
            static function(string $table,array $row) use ($restored,&$counts):void {
                $cols=array_keys($row);
                pairedAssert($cols!==[],'empty imported row');
                foreach($cols as $col) {
                    pairedAssert(is_string($col) &&
                        preg_match('/^[a-z_]+$/D',$col)===1,
                        'unsafe imported column identifier');
                }
                $stmt=$restored->prepare('INSERT INTO '.$table.' ('.
                    implode(',',$cols).') VALUES ('.
                    implode(',',array_fill(0,count($cols),'?')).')');
                $stmt->execute(array_values($row));
                $counts[$table]=($counts[$table]??0)+1;
            }
        );
        foreach($report['rows'] as $table=>$count) {
            pairedAssert(($counts[$table]??0)===$count,
                'restored table count mismatch: '.$table);
        }
        $restored->commit();
    } catch(\Throwable $error) {
        if($restored->inTransaction())$restored->rollBack();
        throw $error;
    }
    // Recover binary media from the *other* snapshot, strictly private 0600.
    $payload=$envelope['payload'];
    foreach($payload['media_data'] as $path=>$encoded) {
        pairedAssert(preg_match('~^site-private/([a-f0-9]{40}\.(?:png|jpg|webp))$~D',
            $path,$match)===1,'unsafe recovery media key');
        $bytes=base64_decode($encoded,true);
        pairedAssert(is_string($bytes),'invalid private recovery bytes');
        $filename=$restoredMedia.'/'.$match[1];
        $fp=fopen($filename,'xb');
        pairedAssert($fp!==false,'refusing overwrite of recovered private image');
        try {
            pairedAssert(chmod($filename,0600) &&
                fwrite($fp,$bytes)===strlen($bytes),'private media recovery failed');
        } finally { fclose($fp); }
    }
    $private=CmsMediaStore::privatePreview(
        $restored,$assetId,$restoredMedia,$root.'/public'
    );
    pairedAssert($private['body']===$fixture,'private image corrupted during joint recovery');
    $template=file_get_contents($root.'/app/Templates/site-v10.html');
    $manifest=file_get_contents($root.'/app/Config/content-fields-v10.json');
    $faq=file_get_contents($root.'/database/seeds/faq-v10.json');
    pairedAssert(CmsRevisions::publishedPage($restored,$template,$manifest,$faq)===
        CmsRevisions::publishedPage($src,$template,$manifest,$faq),
        'site rendering differs after joint recovery');
    pairedAssert((int)$restored->query('SELECT COUNT(*) FROM admin_users')->fetchColumn()===
        (int)$src->query('SELECT COUNT(*) FROM admin_users')->fetchColumn() &&
        (int)$restored->query('SELECT COUNT(*) FROM audit_log')->fetchColumn()===
        (int)$src->query('SELECT COUNT(*) FROM audit_log')->fetchColumn(),
        'admin accounts or audit log lost in joint recovery');
    pairedAssert(!file_exists($root.'/RELEASE_READY') &&
        !file_exists($root.'/public/media/'.$keyName),
        'joint recovery published or authorized the site');
    echo "Stage10: independent encrypted DB+private media snapshots consistent, tampering rejected, full isolated DB and image recovery — PASS\n";
} finally {
    if($created)$src->exec('DROP DATABASE '.$newDb);
    if($assetId!==null) {
        $src->prepare('DELETE FROM media_assets WHERE id=?')->execute([$assetId]);
    }
    foreach(array_reverse($dirs) as $dir) {
        foreach(glob($dir.'/*')?:[] as $entry)if(is_file($entry)||is_link($entry))unlink($entry);
        if(is_dir($dir))rmdir($dir);
    }
}
