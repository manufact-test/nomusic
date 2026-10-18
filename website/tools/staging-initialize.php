<?php
declare(strict_types=1);
/**
 * One-time CLI installer for the isolated CELIKOM owner-review domain.
 * No command-line secrets, no production release marker, never prints passwords.
 */
if (PHP_SAPI !== 'cli' || $argc !== 1) exit(2);
$private = dirname(__DIR__);
$public = dirname($private).'/public_html';
if (!is_dir($public) || !is_file($private.'/staging-config.php')
    || is_file($private.'/app/staging-approved.php')) {
    fwrite(STDERR, "Unsafe or already initialized staging directory\n");
    exit(1);
}
require $private.'/app/bootstrap.php';
use Celikom\Website\CmsDraftStore;
use Celikom\Website\CmsRevisions;
use Celikom\Website\CmsConfig;
use Celikom\Website\Database;
use Celikom\Website\CmsWriteQuiescence;
try {
    $pdo = Database::connect(CmsConfig::databaseSettings());
    $pdo->exec("SET time_zone = '+00:00'");
    if ((int)$pdo->query('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()')->fetchColumn() !== 0) {
        throw new RuntimeException('Staging must use a brand-new empty dedicated database');
    }
    $schema=file_get_contents($private.'/database/migrations/001_website_cms.sql');
    if (!is_string($schema)) throw new RuntimeException('Schema not found');
    $schema=preg_replace('/^--.*$/m','',$schema);
    if (!is_string($schema)) throw new RuntimeException('Schema parse failed');
    foreach (explode(';',$schema) as $ddl) {
        if (trim($ddl)!=='') $pdo->exec(trim($ddl));
    }
    $ownerPass = rtrim(strtr(base64_encode(random_bytes(36)), '+/', '-_'), '=');
    $basicPass = rtrim(strtr(base64_encode(random_bytes(36)), '+/', '-_'), '=');
    $ownerHash = password_hash($ownerPass, PASSWORD_DEFAULT);
    $basicHash = password_hash($basicPass, PASSWORD_BCRYPT);
    if (!is_string($ownerHash) || !is_string($basicHash)) throw new RuntimeException('Hash failure');
    $pdo->prepare('INSERT INTO admin_users(username,password_hash,is_active) VALUES (?, ?, 1)')
        ->execute(['owner',$ownerHash]);
    $admin = (int)$pdo->lastInsertId();
    if ($admin < 1) throw new RuntimeException('Owner creation failed');
    $draft=['content'=>[],'faq'=>[]];
    if (CmsDraftStore::save($pdo,$admin,0,$draft)!==1) {
        throw new RuntimeException('Initial v10 draft failed');
    }
    $template=file_get_contents($private.'/app/Templates/site-v10.html');
    $manifest=file_get_contents($private.'/app/Config/content-fields-v10.json');
    $faq=file_get_contents($private.'/database/seeds/faq-v10.json');
    if (!is_string($template)||!is_string($manifest)||!is_string($faq)) {
        throw new RuntimeException('Approved v10 sources not found');
    }
    $revision=CmsRevisions::publish($pdo,$admin,1,'Исходный утверждённый v10',
        $template,$manifest,$faq);
    if (!is_int($revision) || $revision < 1) throw new RuntimeException('Initial publication failed');
    $htpasswd=$private.'/.htpasswd';
    $credentials=$private.'/staging-owner-credentials.txt';
    foreach ([$htpasswd,$credentials] as $path) {
        if (file_exists($path) || is_link($path)) throw new RuntimeException('Credentials already exist');
    }
    if (file_put_contents($htpasswd, 'review:'.$basicHash."\n", LOCK_EX) === false ||
        !chmod($htpasswd,0600)) throw new RuntimeException('Private Basic Auth file failed');
    $text="CELIKOM CLOSED OWNER REVIEW\n";
    $text.="URL: https://lemonchiffon-narwhal-791953.hostingersite.com/\n";
    $text.="HTTP Basic username: review\nHTTP Basic password: ".$basicPass."\n";
    $text.="CMS URL: https://lemonchiffon-narwhal-791953.hostingersite.com/admin/\n";
    $text.="CMS username: owner\nCMS password: ".$ownerPass."\n";
    $text.="Keep this file private and delete after saving both passwords.\n";
    if (file_put_contents($credentials,$text,LOCK_EX)===false || !chmod($credentials,0600)) {
        throw new RuntimeException('Owner handover failed');
    }
    // The marker is created LAST; missing marker always means closed routes.
    $marker=$private.'/app/staging-approved.php';
    if (file_put_contents($marker,"<?php\nreturn 'CELIKOM_PRIVATE_OWNER_REVIEW_ONLY';\n",LOCK_EX)===false
        || !chmod($marker,0600)) throw new RuntimeException('Private staging marker failed');
    fwrite(STDOUT,"STAGING_INITIALIZED: dedicated database, owner, v10 revision and protected access\n");
} catch (Throwable $e) {
    fwrite(STDERR,"STAGING_NOT_READY: initialization rejected; marker remains absent unless final step succeeded\n");
    exit(1);
}
