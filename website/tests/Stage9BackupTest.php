<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsBackup;
use Celikom\Website\CmsConfig;
use Celikom\Website\Database;
use Celikom\Website\CmsMediaStore;

function backupCheck(bool $test,string $description):void{
    if(!$test)throw new RuntimeException('Backup: '.$description);
}
function backupReject(callable $cb,string $description):void{
    try{$cb();}catch(InvalidArgumentException|RuntimeException|JsonException $e){return;}
    throw new RuntimeException('Backup accepted unsafe condition: '.$description);
}
$base=dirname(__DIR__);
$pdo=Database::connect(CmsConfig::databaseSettings());
$parent=sys_get_temp_dir().'/celikom-backup-'.bin2hex(random_bytes(8));
$backup=$parent.'/backups';
$media=$parent.'/media';
if(!mkdir($parent,0700)||!mkdir($backup,0700)||!mkdir($media,0700)){
    throw new RuntimeException('Could not provision isolated test directories');
}
$fixture=base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true);
if(!is_string($fixture))throw new RuntimeException('Invalid test fixture');
$key=bin2hex(random_bytes(20)).'.png';
$asset=$media.'/'.$key;
file_put_contents($asset,$fixture);
chmod($asset,0600);
try {
    $pdo->prepare(
        'INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,' .
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,1,1,?,?)'
    )->execute(['site-private/'.$key,'test.png','image/png',hash('sha256',$fixture),
        'Приватное тестовое изображение',1]);
    $file=CmsBackup::export($pdo,$backup,$media,$base.'/public');
    backupCheck(is_file($file) && (fileperms($file)&0777)===0600,'backup must be protected');
    $state=CmsBackup::inspect($file);
    backupCheck($state['draft_rows']===1,'expected saved draft snapshot');
    backupCheck($state['revision_rows']===3,'expected three publication revisions');
    backupCheck($state['media_rows']===1,'expected private image in backup');
    backupCheck($state['published_id']!==null,'published revision pointer missing');
    $raw=file_get_contents($file);
    backupCheck(is_string($raw) && str_contains($raw,base64_encode($fixture)),
        'media content not included');
    backupCheck(!str_contains($raw,'valid-Admin!2026-OnlyForCI') &&
        !str_contains($raw,'password_hash') &&
        !str_contains($raw,'login_rate_limits') &&
        !str_contains($raw,'audit_log'),'backup must not include authentication secrets');
    $envelope=json_decode($raw,true,512,JSON_THROW_ON_ERROR);
    $envelope['payload']['tables']['media_assets'][0]['sha256']=str_repeat('a',64);
    $tamper=$backup.'/tampered.json';
    file_put_contents($tamper,json_encode($envelope,JSON_THROW_ON_ERROR));
    backupReject(fn()=>CmsBackup::inspect($tamper),'manifest tampering');
    $envelope=json_decode($raw,true,512,JSON_THROW_ON_ERROR);
    $envelope['payload']['media_data']['site-private/'.$key]=base64_encode('tampered');
    $canonical=json_encode($envelope['payload'],
        JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
    $envelope['sha256']=hash('sha256',$canonical);
    file_put_contents($tamper,json_encode($envelope,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES));
    backupReject(fn()=>CmsBackup::inspect($tamper),'binary tampering with recomputed manifest hash');
    backupReject(fn()=>CmsBackup::export($pdo,$base.'/public',$media,$base.'/public'),
        'no backups under public');
    $corrupt=$asset.'.corrupt';
    rename($asset,$corrupt);
    backupReject(fn()=>CmsBackup::export($pdo,$backup,$media,$base.'/public'),
        'missing private image must fail the complete backup');
    rename($corrupt,$asset);
    backupCheck(CmsBackup::inspect($file)['media_rows']===1,'good backup mutated');
    echo "Stage9: private CMS content backup, media integrity, atomic snapshot, 0600, no auth secrets — PASS\n";
} finally {
    if(isset($file) && is_file($file))unlink($file);
    if(is_file($backup.'/tampered.json'))unlink($backup.'/tampered.json');
    if(is_file($asset))unlink($asset);
    if(isset($corrupt) && is_file($corrupt))unlink($corrupt);
    rmdir($backup);
    rmdir($media);
    rmdir($parent);
}
