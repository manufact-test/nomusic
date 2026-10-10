<?php

declare(strict_types=1);

// CLI-only, pinned private test site. Never prints credentials, signed URLs or media.
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli' || count($argv) !== 2) exit(2);
function guard10(bool $condition): void {
    if (!$condition) throw new RuntimeException('stage10_guard_line_'.(debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS,1)[0]['line']??0));
}
function https10(string $path, string $method = 'GET', ?array $body = null, string $bearer = '', bool $range = false): array {
    guard10(str_starts_with($path, '/api/v1/'));
    usleep(350000); // Avoid bursting local hosting workers/database connection establishment.
    $args = ['curl','--silent','--show-error','--max-time','22','--connect-timeout','10','--max-redirs','0','--proto','=https',
        '--header','Cache-Control: no-store','--header','Origin: https://music.yandex.ru'];
    if ($method === 'HEAD') $args[] = '--head';
    else { $args[] = '--request'; $args[] = $method; }
    if ($bearer !== '') { guard10((bool)preg_match('/^[a-f0-9]{64}$/D', $bearer)); $args[]='--header'; $args[]='Authorization: Bearer '.$bearer; }
    if ($range) { $args[]='--header'; $args[]='Range: bytes=0-3'; }
    $payload = '';
    if ($body !== null) {
        $args[]='--header'; $args[]='Content-Type: application/json'; $args[]='--data-binary'; $args[]='@-';
        $payload=json_encode((object)$body,JSON_THROW_ON_ERROR);
    }
    $args[]='--write-out'; $args[]="\n--CELIKOM-STATUS--:%{http_code}";
    $args[]='https://darkred-camel-588676.hostingersite.com'.$path;
    $proc=proc_open($args,[0=>['pipe','r'],1=>['pipe','w'],2=>['file','/dev/null','w']],$pipes);
    guard10(is_resource($proc));
    if ($payload !== '') fwrite($pipes[0], $payload);
    fclose($pipes[0]); $out=stream_get_contents($pipes[1],16385); fclose($pipes[1]);
    guard10(proc_close($proc)===0 && is_string($out) && strlen($out)<16385);
    $marker="\n--CELIKOM-STATUS--:"; $pos=strrpos($out,$marker); guard10($pos!==false);
    $text=substr($out,0,$pos);
    return [(int)substr($out,$pos+strlen($marker)),json_decode($text,true),$text];
}
function contributions10(PDO $db, array $config, string $token, int $userId): void {
    guard10($config['user_uploads_enabled'] && function_exists('curl_init'));
    $pub=expect10(200,https10('/api/v1/config')); guard10($pub['upload_enabled']===true);
    expect10(401,https10('/api/v1/track-requests','POST',[]));
    $hash=hash_hmac('sha256','contribution.user.'.$userId,$config['analytics_privacy_key']);
    $track='990'.random_int(100000000000,999999999999);
    $q=$db->prepare('SELECT COUNT(*) FROM tracks WHERE service=? AND service_track_id=?');$q->execute(['yandex',$track]);guard10((int)$q->fetchColumn()===0);
    $asset=$db->query("SELECT a.* FROM audio_assets a JOIN track_replacements r ON r.audio_asset_id=a.id WHERE r.id=2")->fetch(PDO::FETCH_ASSOC);
    guard10(is_array($asset));
    $path=$config['storage_path'].'/'.$asset['storage_key'];
    guard10(is_file($path) && !is_link($path) && hash_equals($asset['sha256'],hash_file('sha256',$path)));
    $job=$db->prepare('SELECT * FROM audio_fingerprint_jobs WHERE audio_asset_id=?');$job->execute([$asset['id']]);$beforeJob=$job->fetch(PDO::FETCH_ASSOC);
    $post=static function(string $route,array $fields) use ($token): array {
        usleep(350000);
        $ch=curl_init('https://darkred-camel-588676.hostingersite.com/api/v1/'.$route);
        curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_RETURNTRANSFER=>true,CURLOPT_POSTFIELDS=>$fields,
            CURLOPT_HTTPHEADER=>['Authorization: Bearer '.$token,'Origin: https://music.yandex.ru'],
            CURLOPT_TIMEOUT=>60,CURLOPT_CONNECTTIMEOUT=>10,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_SSL_VERIFYPEER=>true]);
        $text=curl_exec($ch);$code=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);curl_close($ch);
        guard10(is_string($text) && strlen($text)<16384);
        return [$code,json_decode($text,true),$text];
    };
    try {
        $state=expect10(200,https10('/api/v1/tracks/upload-status?service=yandex&track_id='.$track,'GET',null,$token));guard10($state['status']==='none');
        $fields=['service'=>'yandex','track_id'=>$track,'artist'=>'celikom-ci','title'=>'stage10-contribution-check'];
        $suggest=expect10(202,$post('track-requests',$fields));guard10($suggest['status']==='pending');
        $again=expect10(202,$post('track-requests',$fields));guard10($again['request_id']===$suggest['request_id']);
        $fields+=['album'=>'','duration_ms'=>(string)$asset['duration_ms'],'declaration'=>'1','request_id'=>'00000000-0000-4000-8000-'.bin2hex(random_bytes(6)),
            'file'=>new CURLFile($path,'audio/mpeg','synthetic-stage7.mp3')];
        $upload=expect10(202,$post('uploads',$fields));guard10($upload['status']==='pending');
        $repeat=expect10(202,$post('uploads',$fields));guard10($repeat['replacement_id']===$upload['replacement_id'] && $repeat['duplicate']===true);
        $q=$db->prepare("SELECT r.status,r.is_active FROM track_replacements r JOIN tracks t ON t.id=r.track_id WHERE r.id=? AND t.service_track_id=?");
        $q->execute([$upload['replacement_id'],$track]);$row=$q->fetch(PDO::FETCH_ASSOC);guard10($row && $row['status']==='pending' && (int)$row['is_active']===0);
        $state=expect10(200,https10('/api/v1/tracks/upload-status?service=yandex&track_id='.$track,'GET',null,$token));guard10($state['status']==='pending');
        $resolve=expect10(200,https10('/api/v1/resolve?service=yandex&track_id='.$track,'GET',null,$token));guard10($resolve['found']===false);
        echo "Stage10 ordinary-user HTTPS contributions PASS: MP3 and separate no-file suggestion pending-only; dedupe; status; pending denied playback.\n";
    } finally {
        // Delete only random-track QA records, never existing pending #2/#3 or media.
        $db->beginTransaction();
        try {
            $db->prepare('DELETE FROM upload_submissions WHERE uploader_hash=? AND service_track_id=?')->execute([$hash,$track]);
            $q=$db->prepare('SELECT id FROM tracks WHERE service=? AND service_track_id=? FOR UPDATE');$q->execute(['yandex',$track]);$tid=$q->fetchColumn();
            if($tid!==false) {
                $db->prepare("DELETE FROM track_replacements WHERE track_id=? AND status='pending' AND is_active=0")->execute([$tid]);
                $db->prepare('DELETE FROM tracks WHERE id=? AND service_track_id=?')->execute([$tid,$track]);
            }
            $db->prepare('DELETE FROM track_requests WHERE uploader_hash=? AND service_track_id=?')->execute([$hash,$track]);
            $db->prepare('DELETE FROM upload_rate_buckets WHERE identity_hash=?')->execute([$hash]);
            if($beforeJob===false)$db->prepare('DELETE FROM audio_fingerprint_jobs WHERE audio_asset_id=?')->execute([$asset['id']]);
            $db->commit();
        }catch(Throwable $e){if($db->inTransaction())$db->rollBack();throw $e;}
        guard10(hash_equals($asset['sha256'],hash_file('sha256',$path)));
    }
}

function expect10(int $status, array $response): array {
    if ($response[0] !== $status) throw new RuntimeException('stage10_http_expected_'.$status.'_actual_'.$response[0].'_line_'.(debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS,1)[0]['line']??0).(is_array($response[1]) && ($response[1]['error']??'')==='service_unavailable'?'_app_unavailable':(is_array($response[1])?'_json':'_non_json')));
    return is_array($response[1]) ? $response[1] : [];
}
function integrity10(PDO $db, array $config, string $root): array {
    guard10($config['db_name']==='u235811320_celikom' && $config['api_enabled'] && $config['auth_enabled']
        && $config['admin_enabled'] && !$config['analytics_enabled'] 
        && realpath($config['storage_path'])===$root.'/shared/audio');
    $rows=$db->query("SELECT t.service_track_id, r.id, r.status, r.is_active, a.sha256, a.storage_key, a.size_bytes, a.duration_ms
        FROM tracks t JOIN track_replacements r ON r.track_id=t.id JOIN audio_assets a ON a.id=r.audio_asset_id
        WHERE r.id IN (1,2,3) ORDER BY r.id")->fetchAll(PDO::FETCH_ASSOC);
    guard10(count($rows)===3);
    foreach ([[0,'144530503','approved',1],[1,'799133075','pending',0],[2,'38436680','pending',0]] as [$i,$track,$status,$active]) {
        $row=$rows[$i]; guard10($row['service_track_id']===$track && $row['status']===$status && (int)$row['is_active']===$active);
        $path=$root.'/shared/audio/'.$row['storage_key'];
        guard10(!str_contains($row['storage_key'],'..') && is_file($path) && !is_link($path)
            && filesize($path)===(int)$row['size_bytes'] && hash_equals($row['sha256'],hash_file('sha256',$path)));
    }
    return $rows;
}
function smoke10(PDO $db, array $config): void {
    $email='stage10-check-'.bin2hex(random_bytes(12)).'@example.invalid';
    $id=null;
    try {
        $insert=$db->prepare('INSERT INTO users (email,password_hash) VALUES (?,?)');
        $insert->execute([$email,password_hash(bin2hex(random_bytes(32)),PASSWORD_BCRYPT,['cost'=>12])]);
        $id=(int)$db->lastInsertId();
        $db->prepare('INSERT INTO user_email_security (user_id,verified_at) VALUES (?,UTC_TIMESTAMP(6))')->execute([$id]);
        $tokens=[];
        for($i=0;$i<2;$i++) {
            $bytes=random_bytes(16); $bytes[6]=chr((ord($bytes[6])&15)|64); $bytes[8]=chr((ord($bytes[8])&63)|128); $h=bin2hex($bytes);
            $uuid=substr($h,0,8).'-'.substr($h,8,4).'-'.substr($h,12,4).'-'.substr($h,16,4).'-'.substr($h,20);
            $db->prepare('INSERT INTO user_devices (user_id,installation_id) VALUES (?,?)')->execute([$id,$uuid]);
            $device=(int)$db->lastInsertId(); $access=bin2hex(random_bytes(32)); $refresh=bin2hex(random_bytes(32));
            $db->prepare('INSERT INTO user_sessions (user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at)
                VALUES (?,?,?,?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 900 SECOND),DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 90 DAY))')
                ->execute([$id,$device,hash('sha256',$access),hash('sha256',$refresh)]);
            $tokens[]=[$access,$refresh,$uuid];
        }
        $initial=expect10(200,https10('/api/v1/entitlement','GET',null,$tokens[1][0])); guard10($initial['allowed']===false);
        expect10(401,https10('/api/v1/resolve?service=yandex&track_id=144530503'));
        expect10(403,https10('/api/v1/resolve?service=yandex&track_id=144530503','GET',null,$tokens[0][0]));
        $one=expect10(200,https10('/api/v1/auth/activate','POST',[],$tokens[0][0]));
        $two=expect10(200,https10('/api/v1/auth/activate','POST',[],$tokens[1][0]));
        guard10(($one['trial']['activated']??false) && !($two['trial']['activated']??true)
            && $one['trial']['trial_ends_at']===$two['trial']['trial_ends_at']);
        $q=$db->prepare('SELECT TIMESTAMPDIFF(MICROSECOND,valid_from,valid_until) FROM account_trials WHERE user_id=?');
        $q->execute([$id]); guard10((int)$q->fetchColumn()===259200000000);
        $resolve=expect10(200,https10('/api/v1/resolve?service=yandex&track_id=144530503','GET',null,$tokens[0][0]));
        guard10(($resolve['found']??false) && $resolve['replacement_id']===1 && $resolve['duration_ms']===180872
            && str_starts_with($resolve['audio_url'],'/api/v1/audio/1?') && str_contains($resolve['audio_url'],'&sid='));
        $audio=https10($resolve['audio_url'],'GET',null,'',true); guard10($audio[0]===206 && strlen($audio[2])===4);
        expect10(200,https10($resolve['audio_url'],'HEAD'));
        // Exercise every production-size range without the four-byte smoke's pacing.
        $size=(int)$db->query('SELECT size_bytes FROM audio_assets WHERE id=(SELECT audio_asset_id FROM track_replacements WHERE id=1)')->fetchColumn();
        $chunk=524288; $count=0;
        for($offset=0;$offset<$size;$offset+=$chunk) {
            $last=min($size-1,$offset+$chunk-1);
            $args=['curl','--silent','--show-error','--max-time','22','--max-redirs','0','--proto','=https',
                '--header','Origin: https://music.yandex.ru','--header','Cache-Control: no-store',
                '--header','Range: bytes='.$offset.'-'.$last,'--output','/dev/null',
                '--write-out','%{http_code} %{size_download}',
                'https://darkred-camel-588676.hostingersite.com'.$resolve['audio_url']];
            $proc=proc_open($args,[0=>['file','/dev/null','r'],1=>['pipe','w'],2=>['file','/dev/null','w']],$pipes);
            guard10(is_resource($proc)); $result=stream_get_contents($pipes[1],100); fclose($pipes[1]);
            guard10(proc_close($proc)===0);
            if($result!=='206 '.($last-$offset+1)) throw new RuntimeException('stage10_http_expected_206_actual_'.(int)$result.'_line_'.__LINE__);
            $count++;
        }
        echo "Stage10 complete signed MP3 sequential 512KiB ranges PASS: ".$count." chunks.\n";

        foreach (['38436680','799133075'] as $track) {
            $missing=expect10(200,https10('/api/v1/resolve?service=yandex&track_id='.$track,'GET',null,$tokens[0][0]));
            guard10(($missing['found']??true)===false);
        }
        $rotated=expect10(200,https10('/api/v1/auth/refresh','POST',['refresh_token'=>$tokens[0][1],'installation_id'=>$tokens[0][2]]));
        expect10(200,https10('/api/v1/auth/me','GET',null,$rotated['access_token']));
        expect10(200,https10('/api/v1/auth/logout','POST',['refresh_token'=>$rotated['refresh_token'],'installation_id'=>$tokens[0][2]]));
        expect10(403,https10($resolve['audio_url'],'GET',null,'',true));
        // Invoke the same route in CLI to distinguish application errors from HTTP transport.
        $route=new ReflectionMethod(Celikom\Application::class,'route');
        $direct=$route->invoke(new Celikom\Application($config),'GET','/api/v1/entitlement',[],['authorization'=>'Bearer '.$tokens[1][0]],'',[],[]);
        guard10($direct->status===200);
        $second=expect10(200,https10('/api/v1/entitlement','GET',null,$tokens[1][0])); guard10($second['allowed']===true);
        if ($config['user_uploads_enabled']) contributions10($db,$config,$tokens[1][0],$id);
        echo "Stage10 real HTTPS smoke PASS: account trial 3 days; independent devices; user-bearer approved resolve; signed HEAD/206; pending denied; refresh/logout revoke only one device.\n";
    } finally {
        if ($id !== null) {
            guard10((bool)preg_match('/^stage10-check-[a-f0-9]{24}@example\\.invalid$/D',$email));
            $db->beginTransaction();
            try {
                $q=$db->prepare('SELECT id FROM users WHERE id=? AND email=? FOR UPDATE'); $q->execute([$id,$email]); guard10((int)$q->fetchColumn()===$id);
                foreach (['account_trials','entitlement_ledger','user_auth_events','user_sessions','user_devices','user_email_security','users'] as $table)
                    $db->prepare('DELETE FROM '.$table.' WHERE '.($table==='users'?'id':'user_id').'=?')->execute([$id]);
                $db->commit();
            } catch (Throwable $e) { if($db->inTransaction())$db->rollBack(); throw $e; }
        }
    }
}
try {
    $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release=realpath($root.'/current'); $env=$root.'/shared/env';
    guard10(is_link($root.'/current') && is_string($release) && (str_starts_with($release,$root.'/releases/0.4.8-') || str_starts_with($release,$root.'/releases/0.4.9-'))
        && !is_link($root) && !is_link($root.'/shared') && !is_link($env) && is_file($env) && (fileperms($env)&0077)===0);
    $requestPath=realpath($argv[1]);
    guard10(is_string($requestPath) && str_starts_with($requestPath,$root.'/incoming/stage10-')
        && basename($requestPath)==='hostinger-stage10-access-request.json' && filesize($requestPath)<1024);
    $request=json_decode(file_get_contents($requestPath),true,8,JSON_THROW_ON_ERROR);
    guard10(array_keys($request)===['operation','target'] && in_array($request['operation'],['enable','audit','reset-trials','enable-uploads'],true)
        && $request['target']==='hostinger-private-test');
    require $release.'/bootstrap.php'; $config=require $release.'/config/app.php'; $db=Celikom\Database\Connection::open($config);
    $before=integrity10($db,$config,$root);
    foreach (['006_entitlements_ledger.sql','007_account_trials.sql','008_three_day_trial.sql'] as $file) {
        $q=$db->prepare('SELECT sha256 FROM schema_migrations WHERE version=?'); $q->execute([$file]);
        $hash=$q->fetchColumn(); guard10(is_string($hash) && hash_equals($hash,hash_file('sha256',$release.'/migrations/'.$file)));
    }
    if ($request['operation']==='enable-uploads') {
        guard10($config['entitlement_enabled'] && str_starts_with($release,$root.'/releases/0.4.9-'));
        $old=file_get_contents($env); guard10(is_string($old));
        $backup=$root.'/backups/stage10-contributions-env-'.gmdate('YmdTHis').'-'.bin2hex(random_bytes(6));
        guard10(file_put_contents($backup,$old,LOCK_EX)===strlen($old)); chmod($backup,0600);
        $content=preg_replace('/^FEATURE_UPLOADS=.*\\R?/m','',$old);
        $content=rtrim($content)."\nFEATURE_UPLOADS=1\n";
        try {
            $temp=$env.'.uploads-'.bin2hex(random_bytes(6));
            guard10(file_put_contents($temp,$content,LOCK_EX)===strlen($content)); chmod($temp,0600); guard10(rename($temp,$env));
            putenv('FEATURE_UPLOADS=1'); $afterConfig=require $release.'/config/app.php';
            $expected=$config; $expected['user_uploads_enabled']=true;
            guard10($afterConfig===$expected && integrity10($db,$afterConfig,$root)===$before);
            smoke10($db,$afterConfig);
            guard10(integrity10($db,$afterConfig,$root)===$before);
            echo "Stage10 public contributions enable PASS: only FEATURE_UPLOADS changed; accounts/trials/sessions/media/credentials preserved.\n";
        } catch (Throwable $error) { file_put_contents($env,$old,LOCK_EX);chmod($env,0600);throw $error; }
        exit(0);
    }
    if ($request['operation']==='reset-trials') {
        guard10($config['entitlement_enabled'] && str_starts_with($release,$root.'/releases/0.4.8-'));
        // Owner explicitly authorized restarting trial for existing private-test accounts.
        // Backup is immutable. Retry deletes only the ORIGINAL ledger bindings,
        // never a newly started trial. Passwords, verification and sessions untouched.
        $backup=$root.'/backups/stage10-owner-trial-reset-'.basename($release).'.json';
        guard10(!is_link($root.'/backups') && !is_link($backup));
        if (!is_file($backup)) {
            $saved=$db->query('SELECT user_id,ledger_id,valid_from,valid_until FROM account_trials ORDER BY user_id')->fetchAll(PDO::FETCH_ASSOC);
            $data=json_encode(['release'=>basename($release),'trials'=>$saved],JSON_THROW_ON_ERROR);
            $file=fopen($backup,'x'); guard10(is_resource($file)); chmod($backup,0600);
            guard10(fwrite($file,$data)===strlen($data)); fclose($file);
        }
        $saved=json_decode(file_get_contents($backup),true,16,JSON_THROW_ON_ERROR);
        guard10($saved['release']===basename($release) && is_array($saved['trials']));
        $db->beginTransaction();
        try {
            $clear=$db->prepare('DELETE FROM account_trials WHERE user_id=? AND ledger_id=? AND valid_from=? AND valid_until=?');
            $audit=$db->prepare("INSERT INTO entitlement_ledger (user_id,source,reason,valid_from,valid_until)
                VALUES (?,'admin','owner_trial_reset',UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))");
            foreach ($saved['trials'] as $row) {
                $clear->execute([$row['user_id'],$row['ledger_id'],$row['valid_from'],$row['valid_until']]);
                // Zero-duration audit event grants no access; original history remains intact.
                if ($clear->rowCount()===1) $audit->execute([$row['user_id']]);
            }
            $db->commit();
        } catch (Throwable $error) { if($db->inTransaction())$db->rollBack();throw $error; }
        guard10(integrity10($db,$config,$root)===$before);
        smoke10($db,$config);
        echo "Stage10 authorized trial reset PASS: original trial bindings backed up and cleared; next Start grants 3 days; accounts/passwords/email/sessions and ledger history preserved.\n";
        exit(0);
    }
    if ($request['operation']==='audit') {
        guard10($config['entitlement_enabled']);
        smoke10($db,$config);
        echo "Stage10 read-only audit PASS: session playback flag ON, contribution gate checked, approved/pending mappings and private MP3 hashes intact.\n";
        exit(0);
    }
    $old=file_get_contents($env); guard10(is_string($old));
    $backup=$root.'/backups/stage10-env-'.gmdate('YmdTHis').'-'.bin2hex(random_bytes(6));
    guard10(file_put_contents($backup,$old,LOCK_EX)===strlen($old)); chmod($backup,0600);
    $content=preg_replace('/^FEATURE_USER_ENTITLEMENT=.*\\R?/m','',$old);
    $content=rtrim($content)."\nFEATURE_USER_ENTITLEMENT=1\n";
    try {
        $temp=$env.'.stage10-'.bin2hex(random_bytes(6));
        guard10(file_put_contents($temp,$content,LOCK_EX)===strlen($content)); chmod($temp,0600); guard10(rename($temp,$env));
        // Production bootstrap env was already loaded into this CLI process.
        putenv('FEATURE_USER_ENTITLEMENT=1'); $afterConfig=require $release.'/config/app.php';
        guard10($afterConfig['entitlement_enabled'] && integrity10($db,$afterConfig,$root)===$before);
        $expected=$config; $expected['entitlement_enabled']=true; guard10($afterConfig===$expected);
        smoke10($db,$afterConfig);
        guard10(integrity10($db,$afterConfig,$root)===$before);
        echo "Stage10 guarded enable PASS: only FEATURE_USER_ENTITLEMENT changed; historic credentials, admin, audio, pending and public upload gate preserved.\n";
    } catch (Throwable $error) {
        file_put_contents($env,$old,LOCK_EX); chmod($env,0600); throw $error;
    }
} catch (Throwable $failure) {
    $detail=$failure instanceof RuntimeException && preg_match('/^stage10_(?:guard_line_[0-9]+|http_expected_[0-9]+_actual_[0-9]+_line_[0-9]+(?:_app_unavailable|_json|_non_json)?)$/D',$failure->getMessage()) ? $failure->getMessage() : get_class($failure).'_line_'.$failure->getLine();
    if ($failure instanceof PDOException) $detail.='_sqlstate_'.preg_replace('/[^A-Z0-9]/','',(string)($failure->errorInfo[0]??'')).'_driver_'.(int)($failure->errorInfo[1]??0);
    $detail.='_caller_'.implode('_',array_map(static fn(array $frame): string => basename((string)($frame['file']??'')).':'.(int)($frame['line']??0),array_slice($failure->getTrace(),0,3)));
    foreach (['Name or service not known','Temporary failure in name resolution','php_network_getaddresses','Connection refused','No such file or directory','Permission denied','Resource temporarily unavailable','Connection timed out'] as $label) if(str_contains($failure->getMessage(),$label)) $detail.='_'.str_replace(' ','_',$label);
    fwrite(STDERR,"Stage10 guarded operation failed (".$detail."); no private data disclosed.\n"); exit(1);
}
