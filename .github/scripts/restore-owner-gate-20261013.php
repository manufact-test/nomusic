<?php
declare(strict_types=1);
ini_set('display_errors','0');
try {
    if (PHP_SAPI !== 'cli') throw new RuntimeException('cli_only');
    $app='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $snapshots=glob($app.'/backups/stage5/snapshot-*',GLOB_ONLYDIR) ?: [];
    rsort($snapshots,SORT_STRING);
    $source=null;
    foreach ($snapshots as $dir) {
        if (is_link($dir) || realpath($dir)!==$dir || is_link($dir.'/env')) continue;
        $m=json_decode((string)file_get_contents($dir.'/manifest.json'),true,16,JSON_THROW_ON_ERROR);
        if (($m['created_at'] ?? '') >= '2026-10-13T16:28:00' && ($m['created_at'] ?? '') < '2026-10-13T16:28:44') {
            if (!hash_equals((string)$m['env_sha256'],hash_file('sha256',$dir.'/env'))) throw new RuntimeException('hash');
            $source=(string)file_get_contents($dir.'/env');break;
        }
    }
    if ($source===null) throw new RuntimeException('no_verified_snapshot');
    $file=$app.'/shared/env';
    if (is_link($file) || !is_file($file) || (fileperms($file)&0077)) throw new RuntimeException('layout');
    $current=(string)file_get_contents($file);
    $normalize=static function(string $s):string {
        $s=preg_replace('/^(?:UPLOAD_OWNER_TOKEN|FEATURE_OWNER_UPLOADS)\s*=.*(?:\n|$)/m','',$s);
        return rtrim((string)$s,"\r\n");
    };
    if (!hash_equals(hash('sha256',$normalize($source)),hash('sha256',$normalize($current)))) throw new RuntimeException('unrelated_environment_change');
    if (!hash_equals(hash('sha256',$source),hash('sha256',$current))) {
        $tmp=tempnam($app.'/shared','.owner-restore-');
        if ($tmp===false) throw new RuntimeException('temp');
        try {
            if (!chmod($tmp,0600) || file_put_contents($tmp,$source,LOCK_EX)!==strlen($source) || !rename($tmp,$file)) throw new RuntimeException('write');
        } finally {if (is_file($tmp)) unlink($tmp);}
    }
    if (!hash_equals(hash('sha256',$source),hash_file('sha256',$file))) throw new RuntimeException('verify');
    echo "Prior owner gate restored; all other environment settings unchanged.\n";
} catch (Throwable) {fwrite(STDERR,"Bounded owner gate restore failed; no private values disclosed.\n");exit(1);}
