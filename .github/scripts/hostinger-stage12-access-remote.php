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
    foreach(['service_incident_locks','service_incidents','incident_compensations'] as $table) {
        $q=$pdo->prepare('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=?');$q->execute([$table]);
        if (!(int)$q->fetchColumn()) continue;
        $encoded=array_map(static fn($row)=>json_encode($row,JSON_THROW_ON_ERROR),$pdo->query('SELECT * FROM '.$table)->fetchAll(PDO::FETCH_ASSOC));sort($encoded,SORT_STRING);
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
        && is_string($request['expected_release']) && preg_match('/^0\.4\.(?:18|20|22|23)-[a-f0-9]{40}$/D',$request['expected_release'])===1);
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
    } else {
        probe12('/api/v1/rewards',$desired?401:404);probe12('/api/v1/health',200);
        // Read-only render of real grouped history. No account emails or songs
        // are logged; the integrity digest includes policy, ledger and portions.
        $view=new Celikom\Reward\RewardAdminView($pdo);
        $count=(int)$pdo->query('SELECT COUNT(DISTINCT user_id) FROM reward_ledger')->fetchColumn();
        $html=$view->render('read-only-audit',1);
        guard12(substr_count($html,'class="panel reward-account"')===min(25,$count) && !str_contains($html,'class="reward-card"'));
        $id=$pdo->query('SELECT user_id FROM reward_ledger ORDER BY id DESC LIMIT 1')->fetchColumn();
        if($id!==false) {
            $q=$pdo->prepare('SELECT COUNT(*) FROM reward_ledger WHERE user_id=?');$q->execute([$id]);$songs=(int)$q->fetchColumn();
            $html=$view->render('read-only-audit',1,false,(int)$id);
            guard12(substr_count($html,'class="reward-card"')===min(25,$songs));
        }
        if (preg_match('/^0\.4\.(?:22|23)-/',$request['expected_release'])===1) {
            guard12((int)$pdo->query("SELECT COUNT(*) FROM schema_migrations WHERE version='014_service_incidents.sql'")->fetchColumn()===1);
            guard12(!$before['billing_views_enabled'] && !$before['referrals_enabled']);
            $incidents=new Celikom\Incident\IncidentService($pdo);
            guard12(!$incidents->state()['active']);
            foreach(['service_incidents','incident_compensations'] as $table) guard12((int)$pdo->query('SELECT COUNT(*) FROM '.$table)->fetchColumn()===0);
            $html=(new Celikom\Incident\IncidentAdminView($pdo))->render('read-only-audit');
            guard12(str_contains($html,'Объявленных сбоев пока нет.'));
            if (str_starts_with($request['expected_release'],'0.4.23-')) {
                guard12(str_contains($html,'class="incident-form"') && str_contains($html,'<textarea'));
                $panel=new Celikom\Admin\AdminPanel($pdo,new Celikom\Storage\LocalStorageAdapter($before['storage_path']),$before['billing_views_enabled'],$before['reward_eligibility_enabled']);
                $dashboard=(new ReflectionMethod($panel,'dashboard'))->invoke($panel,['role'=>'owner','csrf'=>'read-only-audit'],['tab'=>'incidents']);
                guard12(substr_count($dashboard,'<nav class="nav"')===1 && str_contains($dashboard,'tab=rewards') && str_contains($dashboard,'tab=incidents'));
                fwrite(STDOUT,"Unified admin navigation and spaced incident form read-only audit PASS.\n");
            }
            fwrite(STDOUT,"Stage13 read-only audit PASS: migration, empty incident state and owner view; live outage not declared. Billing/referrals remain disabled.\n");
        }
        guard12(databaseDigest12($pdo)===$digest);
        fwrite(STDOUT,"Grouped account reward history read-only audit PASS. Account and song pages bounded; ledger unchanged.\n");
    }
    fwrite(STDOUT,"Stage12 guarded reward administration PASS. Only reward flag changed; account/device/trial/catalog/media/policy/credentials preserved. Payment application unavailable.\n");
} catch(Throwable $error) {
    fwrite(STDERR,"Stage12 switch failed safely; no private data disclosed.\n");exit(1);
}
