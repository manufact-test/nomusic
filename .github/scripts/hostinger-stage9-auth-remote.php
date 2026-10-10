<?php
declare(strict_types=1);
// Hostinger SSH-only Stage 9 flag switch with self-rollback. Never print credentials.
ini_set('display_errors','0');
if (PHP_SAPI !== 'cli' || count($argv) !== 2) exit(2);

function require9(bool $okay): void { if (!$okay) throw new RuntimeException('guard_at_'.(int)(debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS,1)[0]['line']??0)); }
function https9(string $path, string $method='GET', ?array $body=null, string $bearer=''): array {
    require9(str_starts_with($path,'/api/v1/') || $path==='/admin/audio/1');
    $args=['curl','--silent','--show-error','--max-time','22','--connect-timeout','10',
        '--max-redirs','0','--proto','=https','--request',$method,
        '--header','Accept: application/json','--header','Cache-Control: no-store'];
    $payload='';
    if ($body!==null) {
        $args[]='--header'; $args[]='Content-Type: application/json';
        $args[]='--data-binary'; $args[]='@-';
        $payload=json_encode((object)$body,JSON_THROW_ON_ERROR);
    }
    if ($bearer!=='') {
        require9((bool)preg_match('/^[a-f0-9]{64}$/D',$bearer));
        $args[]='--header'; $args[]='Authorization: Bearer '.$bearer;
    }
    $args[]='--write-out'; $args[]="\n--CELIKOM-STATUS--:%{http_code}";
    $args[]='https://darkred-camel-588676.hostingersite.com'.$path;
    $process=proc_open($args,[0=>['pipe','r'],1=>['pipe','w'],2=>['file','/dev/null','w']],$pipes);
    require9(is_resource($process));
    if ($payload!=='') fwrite($pipes[0],$payload);
    fclose($pipes[0]);
    $text=stream_get_contents($pipes[1],16385);
    fclose($pipes[1]);
    require9(proc_close($process)===0 && is_string($text) && strlen($text)<16385);
    $marker="\n--CELIKOM-STATUS--:";
    $position=strrpos($text,$marker);
    require9($position!==false);
    $status=(int)substr($text,$position+strlen($marker));
    $json=json_decode(substr($text,0,$position),true);
    return [$status,is_array($json)?$json:[]];
}
function code9(int $expected,array $result): array {
    require9($result[0]===$expected);
    return $result[1];
}
function uuid9(): string {
    $b=random_bytes(16); $b[6]=chr((ord($b[6])&15)|64);
    $b[8]=chr((ord($b[8])&63)|128);
    $h=bin2hex($b);
    return substr($h,0,8).'-'.substr($h,8,4).'-'.substr($h,12,4).'-'.substr($h,16,4).'-'.substr($h,20);
}
function invariants9(PDO $db,array $config): void {
    $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    require9($config['environment']==='production' && $config['db_name']==='u235811320_celikom'
        && $config['api_enabled'] && !$config['analytics_enabled'] && $config['admin_enabled']
        && $config['storage_driver']==='local' && realpath($config['storage_path'])===$root.'/shared/audio');
    $mapping=(new Celikom\Repositories\PdoCatalogRepository($db))->findActive('yandex','144530503');
    require9($mapping!==null && (int)$mapping['replacement_id']===1
        && (int)$mapping['duration_ms']===180872);
    $store=new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    require9($store->exists((string)$mapping['storage_key'])
        && $store->getSize((string)$mapping['storage_key'])===(int)$mapping['size_bytes']);
    $audio=$store->openStream((string)$mapping['storage_key']);
    try {
        $ctx=hash_init('sha256');
        while (!feof($audio)) {
            $chunk=fread($audio,65536); require9($chunk!==false); hash_update($ctx,$chunk);
        }
        require9(hash_equals((string)$mapping['sha256'],hash_final($ctx)));
    } finally { fclose($audio); }
    $q=$db->prepare("SELECT COUNT(*) FROM track_replacements r JOIN tracks t ON t.id=r.track_id
        WHERE r.id=? AND r.status='pending' AND r.is_active=0
            AND t.service='yandex' AND t.service_track_id=?");
    foreach ([[2,'799133075'],[3,'38436680']] as [$id,$track]) {
        $q->execute([$id,$track]); require9((int)$q->fetchColumn()===1);
    }
    foreach (['users','user_devices','user_sessions','user_auth_attempts','user_auth_events'] as $table) {
        $q=$db->prepare('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=?');
        $q->execute([$table]); require9((int)$q->fetchColumn()===1);
    }
}
function cleanup9(PDO $db,string $email): void {
    require9((bool)preg_match('/^stage9-check-[a-f0-9]{24}@example\.invalid$/D',$email));
    $db->beginTransaction();
    try {
        $s=$db->prepare('SELECT id FROM users WHERE email=? FOR UPDATE');
        $s->execute([$email]); $id=$s->fetchColumn();
        if ($id!==false) {
            foreach (['user_auth_events','user_sessions','user_devices','users'] as $t) {
                $db->prepare('DELETE FROM '.$t.' WHERE '.($t==='users'?'id':'user_id').'=?')->execute([$id]);
            }
        }
        $db->commit();
    } catch (Throwable $error) {
        if ($db->inTransaction()) $db->rollBack(); throw $error;
    }
}
function smoke9(PDO $db): void {
    $email='stage9-check-'.bin2hex(random_bytes(12)).'@example.invalid';
    $password=bin2hex(random_bytes(32));
    $device1=uuid9(); $device2=uuid9();
    try {
        $config=code9(200,https9('/api/v1/config'));
        require9(($config['features']['auth']??false)===true
            && ($config['features']['replacements']??false)===true
            && ($config['upload_enabled']??null)===false);
        code9(401,https9('/api/v1/auth/me'));
        code9(422,https9('/api/v1/auth/register','POST',
            ['email'=>$email,'password'=>'short','installation_id'=>$device1]));
        $first=code9(201,https9('/api/v1/auth/register','POST',
            ['email'=>$email,'password'=>$password,'installation_id'=>$device1]));
        require9(($first['user']['email']??'')===$email);
        code9(200,https9('/api/v1/auth/me','GET',null,$first['access_token']));
        $second=code9(200,https9('/api/v1/auth/login','POST',
            ['email'=>$email,'password'=>$password,'installation_id'=>$device2]));
        $sessions=code9(200,https9('/api/v1/auth/sessions','GET',null,$first['access_token']));
        require9(count($sessions['sessions']??[])===2);
        $secondId=0;
        foreach ($sessions['sessions'] as $s) {
            if (($s['device_id']??'')===$device2) $secondId=$s['id'];
        }
        require9(is_int($secondId) && $secondId>0);
        $rotated=code9(200,https9('/api/v1/auth/refresh','POST',
            ['refresh_token'=>$first['refresh_token'],'installation_id'=>$device1]));
        code9(401,https9('/api/v1/auth/me','GET',null,$first['access_token']));
        code9(200,https9('/api/v1/auth/me','GET',null,$rotated['access_token']));
        code9(200,https9('/api/v1/auth/sessions/revoke','POST',
            ['session_id'=>$secondId],$rotated['access_token']));
        code9(401,https9('/api/v1/auth/me','GET',null,$second['access_token']));
        code9(200,https9('/api/v1/auth/logout','POST',
            ['refresh_token'=>$rotated['refresh_token'],'installation_id'=>$device1]));
        code9(401,https9('/api/v1/auth/me','GET',null,$rotated['access_token']));
        code9(401,https9('/api/v1/resolve?service=yandex&track_id=144530503'));
        code9(403,https9('/admin/audio/1'));
    } finally { cleanup9($db,$email); }
}
try {
    $base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $env=$base.'/shared/env';
    $release=realpath($base.'/current');
    require9($release!==false && is_link($base.'/current')
        && str_starts_with($release,$base.'/releases/0.4.5-')
        && !is_link($base) && !is_link($base.'/shared') && !is_link($env)
        && is_file($env) && (fileperms($env)&0077)===0
        && !is_link($base.'/backups'));
    $requestPath=realpath($argv[1]);
    require9(is_string($requestPath) && str_starts_with($requestPath,$base.'/incoming/stage9-')
        && basename($requestPath)==='stage9-auth-request.json'
        && filesize($requestPath)<1024);
    $request=json_decode((string)file_get_contents($requestPath),true,8,JSON_THROW_ON_ERROR);
    require9(is_array($request) && array_keys($request)===['operation','target']
        && in_array($request['operation'],['enable','disable'],true)
        && $request['target']==='hostinger-private-test');
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    $db=Celikom\Database\Connection::open($config);
    invariants9($db,$config);
    $m=$db->prepare('SELECT sha256 FROM schema_migrations WHERE version=?');
    $m->execute(['004_user_identity.sql']); $stored=$m->fetchColumn();
    require9(is_string($stored) && hash_equals($stored,
        hash_file('sha256',$release.'/migrations/004_user_identity.sql')));
    $original=(string)file_get_contents($env);
    require9(strlen($original)>200 && strlen($original)<16384);
    $snapshot=glob($base.'/backups/stage5/snapshot-*/manifest.json')?:[];
    rsort($snapshot,SORT_STRING);
    require9(count($snapshot)>0);
    $manifest=json_decode((string)file_get_contents($snapshot[0]),true,16,JSON_THROW_ON_ERROR);
    require9(($manifest['format']??null)===1 && count($manifest['tables']??[])===21
        && isset($manifest['tables']['user_sessions'])
        && hash_equals((string)$manifest['env_sha256'],hash('sha256',$original)));
    $desired=$request['operation']==='enable';
    preg_match_all('/^FEATURE_USER_AUTH=(?:0|1)$/m',$original,$matches);
    preg_match_all('/^\s*FEATURE_USER_AUTH\s*=/m',$original,$allFlags);
    require9(count($matches[0])<=1 && count($matches[0])===count($allFlags[0]));
    if ((bool)$config['auth_enabled']===$desired) {
        $current=code9(200,https9('/api/v1/config'));
        require9(($current['features']['auth']??null)===$desired);
        echo "Stage 9 auth already in requested state; HTTPS verified.\n";
        exit(0);
    }
    if ($matches[0]) {
        $next=preg_replace('/^FEATURE_USER_AUTH=(?:0|1)$/m',
            'FEATURE_USER_AUTH='.($desired?'1':'0'),$original,1,$count);
        require9(is_string($next) && $count===1);
    } else {
        $next=rtrim($original,"\r\n")."\nFEATURE_USER_AUTH=".($desired?'1':'0')."\n";
    }
    $backup=$base.'/backups/stage9-env-'.gmdate('YmdTHis').'-'.bin2hex(random_bytes(8));
    require9(!file_exists($backup) && copy($env,$backup) && chmod($backup,0600));
    $changed=false;
    try {
        $temp=tempnam($base.'/shared','.stage9-');
        require9(is_string($temp) && chmod($temp,0600)
            && file_put_contents($temp,$next,LOCK_EX)===strlen($next)
            && rename($temp,$env));
        $changed=true;
        $response=code9(200,https9('/api/v1/config'));
        require9(($response['features']['auth']??null)===$desired
            && ($response['features']['replacements']??null)===true
            && ($response['upload_enabled']??null)===false);
        if ($desired) smoke9($db);
        else code9(404,https9('/api/v1/auth/me'));
        code9(200,https9('/api/v1/health'));
        invariants9($db,$config);
        require9(hash_equals(hash('sha256',$next),hash_file('sha256',$env)));
    } catch (Throwable $error) {
        if ($changed) {
            $rollback=tempnam($base.'/shared','.stage9-rollback-');
            if ($rollback!==false) {
                chmod($rollback,0600);
                if (copy($backup,$rollback)) rename($rollback,$env);
                if (is_file($rollback)) unlink($rollback);
            }
        }
        throw $error;
    }
    echo "Stage 9 private user auth ".($desired?'enabled':'disabled')
        ."; HTTPS, two devices, revocation, backup and protected media verified.\n";
} catch (Throwable $error) {
    $reason = preg_match('/^guard_at_[0-9]{1,4}$/D',$error->getMessage()) ? $error->getMessage() : 'other';
    fwrite(STDERR,"Stage 9 auth switch refused or reverted: ".$reason."; private information not logged.\n");
    exit(1);
}
