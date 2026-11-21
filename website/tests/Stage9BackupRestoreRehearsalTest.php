<?php
declare(strict_types=1);
/**
 * CI-only content recovery in an always-new disposable database.
 * No production command, never restores owner accounts or publication gates.
 */
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\CmsBackup;
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsDraftStore;
use Celikom\Website\CmsMediaStore;
use Celikom\Website\CmsRevisions;
use Celikom\Website\CmsEditor;
use Celikom\Website\Database;
function recoveryAssert(bool $ok,string $why):void {
    if(!$ok)throw new RuntimeException('Recovery: '.$why);
}
$cfg=CmsConfig::databaseSettings();
if(getenv('CI')!=='true' || getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
    $cfg['dbname']!=='celikom_site_test' || $cfg['host']!=='127.0.0.1') {
    throw new RuntimeException('Rehearsal is restricted to explicitly configured CI MySQL');
}
$src=Database::connect($cfg);
$root=dirname(__DIR__);
$temp=sys_get_temp_dir().'/celikom-recovery-'.bin2hex(random_bytes(12));
$media=$temp.'/media';$destination=$temp.'/recovered';$backup=$temp.'/backup';
if(!mkdir($temp,0700)||!mkdir($media,0700)||!mkdir($destination,0700)||
    !mkdir($backup,0700))throw new RuntimeException('Private temp setup failed');
$db='celikom_site_restore_test_'.bin2hex(random_bytes(6));
$created=false;$sourceAssetId=null;
try {
    $png=base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true);
    recoveryAssert(is_string($png),'sample image');
    $filename=bin2hex(random_bytes(20)).'.png';
    file_put_contents($media.'/'.$filename,$png);chmod($media.'/'.$filename,0600);
    $src->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,'.
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)')
        ->execute(['site-private/'.$filename,'test.png','image/png',
            hash('sha256',$png),1,1,'Only CI',1]);
    $sourceAssetId=(int)$src->lastInsertId();
    $file=CmsBackup::export($src,$backup,$media,$root.'/public');
    $check=CmsBackup::inspect($file);
    recoveryAssert($check['media_rows']===1 && $check['revision_rows']>=1,
        'complete source fixture must be present');
    $payload=json_decode((string)file_get_contents($file),true,512,JSON_THROW_ON_ERROR)['payload'];
    $html=file_get_contents($root.'/app/Templates/site-v10.html');
    $manifest=file_get_contents($root.'/app/Config/content-fields-v10.json');
    $faq=file_get_contents($root.'/database/seeds/faq-v10.json');
    $src->exec('CREATE DATABASE '.$db.' CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');
    $created=true;
    $dst=Database::connect([...$cfg,'dbname'=>$db]);
    $sql=preg_replace('/^--.*$/m','',
        (string)file_get_contents($root.'/database/migrations/001_website_cms.sql'));
    foreach(explode(';',$sql) as $statement) {
        if(trim($statement)!=='')$dst->exec(trim($statement));
    }
    recoveryAssert((int)$dst->query('SELECT COUNT(*) FROM admin_users')->fetchColumn()===0 &&
        (int)$dst->query('SELECT COUNT(*) FROM content_revisions')->fetchColumn()===0,
        'destination must begin empty');
    $dst->exec("INSERT INTO admin_users(id,username,password_hash,is_active)
        VALUES(1,'disabled-recovery-holder','disabled',0)");
    $dst->beginTransaction();
    try {
        foreach($payload['tables']['content_revisions'] as $rev) {
            $dst->prepare('INSERT INTO content_revisions(id,snapshot_json,change_note,created_by,created_at)
                VALUES(?,?,?,1,?)')->execute([
                    $rev['id'],$rev['snapshot_json'],$rev['change_note'],$rev['created_at']
                ]);
        }
        foreach($payload['tables']['content_drafts'] as $draft) {
            CmsEditor::validate($html,$manifest,$faq,
                json_decode($draft['draft_json'],true,512,JSON_THROW_ON_ERROR));
            $dst->prepare('INSERT INTO content_drafts(id,draft_json,optimistic_version,updated_by,updated_at)
                VALUES(?,?,?,1,?)')->execute([
                    $draft['id'],$draft['draft_json'],$draft['optimistic_version'],$draft['updated_at']
                ]);
        }
        foreach($payload['tables']['media_assets'] as $asset) {
            $key=$asset['storage_key'];
            recoveryAssert(is_string($key) &&
                preg_match('~^site-private/([a-f0-9]{40}\.(?:png|jpg|webp))$~D',$key,$match)===1,
                'recovery path not allowed');
            $bytes=base64_decode($payload['media_data'][$key],true);
            recoveryAssert(is_string($bytes) && strlen($bytes)<=CmsMediaStore::MAX_BYTES &&
                hash_equals((string)$asset['sha256'],hash('sha256',$bytes)),
                'recovered binary digest invalid');
            $dest=$destination.'/'.$match[1];
            $fd=fopen($dest,'xb');
            recoveryAssert($fd!==false,'overwrite forbidden');
            try {
                recoveryAssert(chmod($dest,0600) &&
                    fwrite($fd,$bytes)===strlen($bytes),'restore media write');
            } finally {fclose($fd);}
            $dst->prepare('INSERT INTO media_assets(id,storage_key,original_filename,mime_type,sha256,
                pixel_width,pixel_height,alt_text,created_by,created_at,is_active)
                VALUES(?,?,?,?,?,?,?,?,1,?,?)')->execute([
                    $asset['id'],$key,$asset['original_filename'],$asset['mime_type'],
                    $asset['sha256'],$asset['pixel_width'],$asset['pixel_height'],
                    $asset['alt_text'],$asset['created_at'],$asset['is_active']
                ]);
            recoveryAssert(CmsMediaStore::privatePreview(
                $dst,(int)$asset['id'],$destination,$root.'/public'
            )['body']===$bytes,'recovered media is not usable privately');
        }
        foreach($payload['tables']['content_revisions'] as $rev) {
            $dst->prepare('UPDATE site_state SET published_revision_id=?,updated_by=1 WHERE id=1')
                ->execute([$rev['id']]);
            CmsRevisions::publishedPage($dst,$html,$manifest,$faq);
        }
        $dst->prepare('UPDATE site_state SET published_revision_id=?,updated_by=1 WHERE id=1')
            ->execute([$payload['tables']['site_state'][0]['published_revision_id']]);
        $dst->commit();
    } catch(\Throwable $e) {
        if($dst->inTransaction())$dst->rollBack();
        throw $e;
    }
    recoveryAssert(CmsDraftStore::get($dst)===CmsDraftStore::get($src),
        'draft and optimistic version parity');
    recoveryAssert(CmsRevisions::publishedPage($dst,$html,$manifest,$faq)===
        CmsRevisions::publishedPage($src,$html,$manifest,$faq),
        'published page parity');
    recoveryAssert(CmsRevisions::publishedId($dst)===CmsRevisions::publishedId($src),
        'published revision ID parity');
    recoveryAssert((int)$dst->query('SELECT COUNT(*) FROM content_revisions')->fetchColumn()===
        $check['revision_rows'],'history length');
    recoveryAssert((int)$dst->query('SELECT COUNT(*) FROM admin_users WHERE is_active=1')->fetchColumn()===0 &&
        (int)$dst->query('SELECT COUNT(*) FROM audit_log')->fetchColumn()===0 &&
        (int)$dst->query('SELECT COUNT(*) FROM login_rate_limits')->fetchColumn()===0,
        'restore imported auth or audit state');
    echo "Stage9: private content backup restored in a new CI-only MySQL DB, revisions/draft/media match, no user credentials — PASS\n";
} finally {
    if($created)$src->exec('DROP DATABASE '.$db);
    if($sourceAssetId!==null)$src->prepare('DELETE FROM media_assets WHERE id=?')->execute([$sourceAssetId]);
    foreach([$media,$destination,$backup] as $dir) {
        foreach(glob($dir.'/*') ?: [] as $path)@unlink($path);
        rmdir($dir);
    }
    rmdir($temp);
}
