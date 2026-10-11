<?php

declare(strict_types=1);

// Fixed Hostinger site, explicit release pin. Only one default-off flag can change.
ini_set('display_errors','0');
if(PHP_SAPI!=='cli' || count($argv)!==2) exit(2);
function guard12(bool $condition):void {if(!$condition) throw new RuntimeException('stage12_guard');}
function databaseDigest12(PDO $pdo):string {
    $hash=hash_init('sha256');
    foreach(['users','user_devices','user_sessions','user_email_security','account_trials','entitlement_ledger',
        'admins','tracks','audio_assets','track_replacements','reward_ledger','reward_policy','reward_allocations','referrals','referral_codes'] as $table) {
        $rows=$pdo->query('SELECT * FROM '.$table)->fetchAll(PDO::FETCH_ASSOC);
        $encoded=array_map(static fn($row)=>json_encode($row,JSON_THROW_ON_ERROR),$rows);sort($encoded,SORT_STRING);
        hash_update($hash,$table.json_encode($encoded,JSON_THROW_ON_ERROR));
    }
    return hash_final($hash);
}
function probe12(string $path,int $expected):void {
    $url='https://darkred-camel-588676.hostingersite.com'.$path;
    $args=['curl','--silent','--show-error','--max-time','25','--connect-timeout','10','--max-redirs','0','--proto','=https',
        '--header','Cache-Control: no-store','--output','/dev/null','--write-out','%{http_code}',$url];
    $process=proc_open($args,[0=>['file','/dev/null','r'],1=>['pipe','w'],2=>['file','/dev/null','w']],$pipes);
    guard12(is_resource($process));$code=stream_get_contents($pipes[1],10);fclose($pipes[1]);guard12(proc_close($process)===0 && (int)$code===$expected);
}
try {
    $app='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';$shared=$app.'/shared';
    guard12(is_link($app.'/current') && !is_link($app) && !is_link($shared) && !is_link($shared.'/env'));
    $requestPath=realpath($argv[1]);guard12($requestPath!==false && str_starts_with($requestPath,$app.'/incoming/stage12-')
        && basename($requestPath)==='hostinger-stage12-access-request.json' && filesize($requestPath)<1024);
    $request=json_decode((string)file_get_contents($requestPath),true,8,JSON_THROW_ON_ERROR);
    guard12(is_array($request) && array_keys($request)===['operation','target','expected_release']
        && $request['target']==='hostinger-private-test' && in_array($request['operation'],['enable','disable','audit'],true)
        && is_string($request['expected_release']) && preg_match('/^0\.4\.17-[a-f0-9]{40}$/D',$request['expected_release'])===1);
    $release=realpath($app.'/current');guard12($release===$app.'/releases/'.$request['expected_release']);
    require $release.'/bootstrap.php';$before=require $release.'/config/app.php';
    guard12($before['environment']==='production' && $before['auth_enabled'] && $before['admin_enabled']
        && $before['entitlement_enabled'] && $before['user_uploads_enabled'] && $before['api_enabled'] && !$before['analytics_enabled']);
    $pdo=Celikom\Database\Connection::open($before);
    $q=$pdo->prepare('SELECT COUNT(*) FROM schema_migrations WHERE version IN (?,?,?)');$q->execute(['011_reward_eligibility.sql','012_reward_policy.sql','013_automatic_rewards.sql']);guard12((int)$q->fetchColumn()===3);
    $mapping=(new Celikom\Repositories\PdoCatalogRepository($pdo))->findActive('yandex','144530503');
    guard12($mapping!==null && (int)$mapping['replacement_id']===1 && (int)$mapping['duration_ms']===180872);
    $audio=$before['storage_path'].'/'.$mapping['storage_key'];guard12(is_file($audio) && !is_link($audio) && hash_equals($mapping['sha256'],hash_file('sha256',$audio)));
    $digest=databaseDigest12($pdo);$env=$shared.'/env';$old=(string)file_get_contents($env);guard12($old!=='' && !(fileperms($env)&0077));
    $operation=$request['operation'];$desired=$operation==='enable'?true:($operation==='disable'?false:$before['reward_eligibility_enabled']);
    $strip=static fn(string $text):string=>rtrim((string)preg_replace('/^FEATURE_REWARD_ELIGIBILITY=.*\R?/m','',$text));
    if ($operation!=='audit') {
        $backupDir=$app.'/backups/stage12';guard12(!is_link($backupDir));
        if(!is_dir($backupDir)) guard12(mkdir($backupDir,0700));
        $backup=$backupDir.'/env-'.gmdate('YmdHis').'-'.bin2hex(random_bytes(6));
        guard12(file_put_contents($backup,$old,LOCK_EX)===strlen($old));chmod($backup,0600);
        $content=$strip($old)."\nFEATURE_REWARD_ELIGIBILITY=".($desired?'1':'0')."\n";
        guard12($strip($content)===$strip($old));$temporary=$shared.'/env-stage12-'.bin2hex(random_bytes(8));
        try {
            guard12(file_put_contents($temporary,$content,LOCK_EX)===strlen($content));chmod($temporary,0600);guard12(rename($temporary,$env));
            putenv('FEATURE_REWARD_ELIGIBILITY='.($desired?'1':'0'));$after=require $release.'/config/app.php';
            guard12($after['reward_eligibility_enabled']===$desired);unset($before['reward_eligibility_enabled'],$after['reward_eligibility_enabled']);guard12($after===$before);
            probe12('/api/v1/rewards',$desired?401:404);probe12('/api/v1/health',200);
            guard12(databaseDigest12($pdo)===$digest);
        } catch(Throwable $error) {
            file_put_contents($env,$old,LOCK_EX);chmod($env,0600);if(is_file($temporary)) unlink($temporary);throw $error;
        }
    } else {probe12('/api/v1/rewards',$desired?401:404);probe12('/api/v1/health',200);guard12(databaseDigest12($pdo)===$digest);}
    fwrite(STDOUT,"Stage12 guarded reward administration PASS. Only reward flag changed; account/device/trial/catalog/media/policy/credentials preserved. Payment application unavailable.\n");
} catch(Throwable $error) {
    fwrite(STDERR,"Stage12 switch failed safely; no private data disclosed.\n");exit(1);
}
