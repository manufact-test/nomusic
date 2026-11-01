<?php
declare(strict_types=1);
/**
 * CI ONLY: encrypted full CMS DB backup, corruption detection and recovery
 * into a RANDOM, disposable MySQL schema. No production DB or media writes.
 */
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\CmsFullDbBackup;
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsRevisions;
use Celikom\Website\Database;
function fullCheck(bool $ok,string $why):void {
    if(!$ok)throw new RuntimeException('Full DB backup: '.$why);
}
function fullReject(callable $task,string $why):void {
    try{$task();}catch(\Throwable $error){return;}
    throw new RuntimeException('Full DB backup accepted invalid state: '.$why);
}
$cfg=CmsConfig::databaseSettings();
if(getenv('CI')!=='true' ||
    getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
    $cfg['dbname']!=='celikom_site_test' || $cfg['host']!=='127.0.0.1') {
    throw new RuntimeException('Encrypted backup integration requires isolated CI MySQL');
}
$pdo=Database::connect($cfg);
$base=dirname(__DIR__);
$parent=sys_get_temp_dir().'/celikom-full-encrypted-'.bin2hex(random_bytes(8));
$store=$parent.'/encrypted';
if(!mkdir($parent,0700)||!mkdir($store,0700)) {
    throw new RuntimeException('Cannot provision disposable private backup folder');
}
$db='celikom_site_fullrestore_test_'.bin2hex(random_bytes(6));
$created=false;
$backup=null;
$key=random_bytes(32);
try {
    fullReject(fn()=>CmsFullDbBackup::export($pdo,$base.'/public',$base.'/public',$key),
        'backup inside public web root');
    fullReject(fn()=>CmsFullDbBackup::export($pdo,$store,$base.'/public','short'),
        'short encryption key');
    fullReject(fn()=>CmsFullDbBackup::keyFromEnv(),'unset production key');
    putenv('CELIKOM_SITE_FULL_BACKUP_KEY='.base64_encode($key));
    fullCheck(CmsFullDbBackup::keyFromEnv()===$key,'independent key decoder');
    $backup=CmsFullDbBackup::export($pdo,$store,$base.'/public',$key);
    fullCheck(is_file($backup) && !is_link($backup) &&
        (fileperms($backup)&0777)===0600,'encrypted output must be 0600 regular file');
    $raw=file_get_contents($backup);
    fullCheck(is_string($raw) &&
        str_starts_with($raw,"CELIKOM_ENCRYPTED_SITE_DB_V1\n") &&
        !str_contains($raw,'cms.revision.published') &&
        !str_contains($raw,'password_hash'),
        'plaintext-sensitive database values leaked to encrypted backup');
    $preview=CmsFullDbBackup::inspect($backup,$key);
    fullCheck($preview['encrypted']===true &&
        $preview['tables']['admin_users']===1 &&
        $preview['tables']['content_revisions']>=3 &&
        $preview['tables']['content_drafts']===1 &&
        $preview['tables']['site_state']===1 &&
        $preview['tables']['audit_log']>=1,
        'full database or admin/audit tables were omitted');
    fullReject(fn()=>CmsFullDbBackup::inspect($backup,random_bytes(32)),
        'wrong decryption key');
    $bad=$store.'/tampered.sbox';
    $changed=$raw;
    $i=strlen($changed)-20;
    $changed[$i]=chr(ord($changed[$i]) ^ 1);
    file_put_contents($bad,$changed);
    chmod($bad,0600);
    fullReject(fn()=>CmsFullDbBackup::inspect($bad,$key),'ciphertext tampering');
    file_put_contents($bad,substr($raw,0,-6));
    fullReject(fn()=>CmsFullDbBackup::inspect($bad,$key),'truncated backup');
    file_put_contents($bad,$raw.'trailing');
    fullReject(fn()=>CmsFullDbBackup::inspect($bad,$key),'trailing untrusted data');
    unlink($bad);
    $pdo->exec('CREATE DATABASE '.$db.' CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');
    $created=true;
    $restored=Database::connect([...$cfg,'dbname'=>$db]);
    $sql=preg_replace('/^--.*$/m','',
        (string)file_get_contents($base.'/database/migrations/001_website_cms.sql'));
    foreach(explode(';',$sql) as $statement) {
        if(trim($statement)!=='')$restored->exec(trim($statement));
    }
    // The only factory row from the migration will be imported from snapshot.
    $restored->exec('DELETE FROM site_state WHERE id=1');
    $restored->beginTransaction();
    try {
        $actualCounts=array_fill_keys(array_keys($preview['tables']),0);
        $scanned=CmsFullDbBackup::inspect($backup,$key,
            static function(string $table,array $row) use ($restored,&$actualCounts):void {
                $columns=array_keys($row);
                if($columns===[])throw new RuntimeException('Empty database row');
                foreach($columns as $column) {
                    if(preg_match('/^[a-z_]+$/D',$column)!==1) {
                        throw new RuntimeException('Invalid MySQL column identifier');
                    }
                }
                $query='INSERT INTO '.$table.' ('.implode(',',$columns).') VALUES ('.
                    implode(',',array_fill(0,count($columns),'?')).')';
                $stmt=$restored->prepare($query);
                if(!$stmt->execute(array_values($row))) {
                    throw new RuntimeException('Encrypted recovery row import failed');
                }
                ++$actualCounts[$table];
            }
        );
        fullCheck($scanned['tables']===$actualCounts,
            'recovered encrypted row count mismatch');
        $restored->commit();
    } catch(\Throwable $error) {
        if($restored->inTransaction())$restored->rollBack();
        throw $error;
    }
    foreach($preview['tables'] as $table=>$count) {
        fullCheck((int)$restored->query('SELECT COUNT(*) FROM '.$table)->fetchColumn()===$count,
            'restored database lost rows in '.$table);
    }
    $template=file_get_contents($base.'/app/Templates/site-v10.html');
    $manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
    $faq=file_get_contents($base.'/database/seeds/faq-v10.json');
    fullCheck(CmsRevisions::publishedPage($restored,$template,$manifest,$faq)===
        CmsRevisions::publishedPage($pdo,$template,$manifest,$faq),
        'live CMS page differs after encrypted full backup recovery');
    $srcHash=$pdo->query("SELECT password_hash FROM admin_users WHERE username='owner'")
        ->fetchColumn();
    $dstHash=$restored->query("SELECT password_hash FROM admin_users WHERE username='owner'")
        ->fetchColumn();
    fullCheck(is_string($srcHash)&&$srcHash===$dstHash,
        'admin record not recovered identically');
    fullCheck(!is_file($base.'/public/'.basename($backup)),
        'encrypted database accidentally appeared in public root');
    echo "Stage10: encrypted full website DB backup, wrong-key/tamper/EOF rejection, disposable full MySQL recovery — PASS\n";
} finally {
    putenv('CELIKOM_SITE_FULL_BACKUP_KEY');
    if($created)$pdo->exec('DROP DATABASE '.$db);
    foreach(glob($store.'/*')?:[] as $item)if(is_file($item))unlink($item);
    rmdir($store);
    rmdir($parent);
}
