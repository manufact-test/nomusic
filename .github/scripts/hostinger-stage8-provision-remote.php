<?php
declare(strict_types=1);
// Private SSH-only Stage 8 bootstrap. No HTTP route, no logging of passwords or SQL.
ini_set('display_errors','0');
if (PHP_SAPI !== 'cli' || count($argv) !== 1) exit(2);
try {
    $site = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
    $root = $site . '/celikom';
    $release = realpath($root . '/current');
    $env = $root . '/shared/env';
    if (!is_link($root . '/current') || !$release
        || !str_starts_with($release, $root . '/releases/')
        || is_link($root) || is_link($root . '/shared') || is_link($env)
        || !is_file($env) || (fileperms($env) & 0077)
        || !is_file($release . '/src/Admin/AdminAuth.php')
        || !is_file($release . '/bin/admin-create.php')
        || !is_dir($site . '/public_html')) throw new RuntimeException('layout');
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['db_name'] !== 'u235811320_celikom'
        || $config['environment'] !== 'production'
        || !$config['api_enabled'] || $config['analytics_enabled']
        || $config['storage_driver'] !== 'local'
        || realpath($config['storage_path']) !== $root . '/shared/audio') {
        throw new RuntimeException('environment');
    }
    $pdo = Celikom\Database\Connection::open($config);
    foreach (['admins','admin_sessions','audit_log','track_request_reviews','reports','track_requests'] as $t) {
        $q=$pdo->prepare('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=?');
        $q->execute([$t]);
        if ((int)$q->fetchColumn()!==1) throw new RuntimeException('migration');
    }
    $approved=(new Celikom\Repositories\PdoCatalogRepository($pdo))->findActive('yandex','144530503');
    if (!$approved || (int)$approved['replacement_id']!==1
        || (int)$approved['duration_ms']!==180872) throw new RuntimeException('original');
    $storage=new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    if (!$storage->exists((string)$approved['storage_key'])
        || $storage->getSize((string)$approved['storage_key']) !== (int)$approved['size_bytes']) {
        throw new RuntimeException('audio');
    }
    $fp=$storage->openStream((string)$approved['storage_key']);
    $hash=hash_init('sha256');
    while(!feof($fp)) { $chunk=fread($fp,65536); if ($chunk===false) throw new RuntimeException('audio'); hash_update($hash,$chunk); }
    fclose($fp);
    if (!hash_equals((string)$approved['sha256'],hash_final($hash))) throw new RuntimeException('audio');
    if ((int)$pdo->query("SELECT COUNT(*) FROM track_replacements WHERE id IN (2,3) AND status <> 'pending'")->fetchColumn() !== 0) throw new RuntimeException('pending');
    if ((int)$pdo->query('SELECT COUNT(*) FROM admins')->fetchColumn()!==0) throw new RuntimeException('account_exists');
    $password=trim((string)stream_get_contents(STDIN,512));
    if (!preg_match('/^[a-f0-9]{64}$/D',$password)) throw new RuntimeException('input');
    $current=(string)file_get_contents($env);
    if ($current==='' || strlen($current)>16000) throw new RuntimeException('env');
    $next=preg_replace('/^(?:FEATURE_ADMIN|FEATURE_OWNER_REPORTS)\\s*=.*(?:\\r?\\n|$)/m','',$current);
    if (!is_string($next)) throw new RuntimeException('env');
    $next=rtrim($next,"\r\n")."\nFEATURE_ADMIN=1\nFEATURE_OWNER_REPORTS=0\n";
    $pdo->beginTransaction();
    try {
        $stmt=$pdo->prepare("INSERT INTO admins (login,password_hash,role,enabled) VALUES ('owner',?,'owner',1)");
        $stmt->execute([password_hash($password,PASSWORD_DEFAULT)]);
        unset($password);
        // Durable, private pre-change configuration copy; Stage 8 DB/media snapshot was
        // separately verified before migration and before this bootstrap action.
        $bak=$root.'/backups/stage8-owner-env-'.gmdate('YmdTHis').'-'.bin2hex(random_bytes(4));
        if (!copy($env,$bak) || !chmod($bak,0600)) throw new RuntimeException('backup');
        $tmp=tempnam($root.'/shared','.admin-env-');
        if ($tmp===false) throw new RuntimeException('write');
        try {
            if (!chmod($tmp,0600) || file_put_contents($tmp,$next,LOCK_EX)!==strlen($next)
                || !rename($tmp,$env)) throw new RuntimeException('write');
        } finally { if (file_exists($tmp)) unlink($tmp); }
        $pdo->commit();
    } catch (Throwable $error) {
        if ($pdo->inTransaction()) $pdo->rollBack();
        throw $error;
    }
    echo "Stage 8 private admin owner created and gated console enabled; original audio verified unchanged.\n";
} catch (Throwable) {
    fwrite(STDERR,"Stage 8 private owner bootstrap refused; no secret data logged.\n");
    exit(1);
}
