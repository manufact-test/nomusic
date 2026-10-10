<?php
declare(strict_types=1);

// Private SSH-only SMTP configuration and test delivery. Secrets read from STDIN, never argv.
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli' || count($argv) !== 2) exit(2);
function mail9Guard(bool $condition): void {
    if (!$condition) throw new RuntimeException('mail_provision_guard');
}
try {
    $base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $env=$base.'/shared/env';
    $release=realpath($base.'/current');
    mail9Guard($release!==false && is_link($base.'/current')
        && str_starts_with($release,$base.'/releases/0.4.5-')
        && !is_link($base.'/shared') && !is_link($env) && !is_link($base.'/backups')
        && is_file($env) && (fileperms($env)&0077)===0
        && is_dir($base.'/backups') && is_dir($base.'/shared'));
    $source=realpath($argv[1]);
    mail9Guard(is_string($source) && str_starts_with($source,$base.'/incoming/stage9-mail-')
        && basename($source)==='hostinger-stage9-mail-request.json' && filesize($source)<512);
    $request=json_decode((string)file_get_contents($source),true,8,JSON_THROW_ON_ERROR);
    mail9Guard(is_array($request) && array_keys($request)===['operation','target']
        && $request['operation']==='provision' && $request['target']==='hostinger-private-test');
    $raw=stream_get_contents(STDIN,8193);
    mail9Guard(is_string($raw) && strlen($raw)>50 && strlen($raw)<8193);
    $payload=json_decode($raw,true,8,JSON_THROW_ON_ERROR);
    mail9Guard(is_array($payload) &&
        array_keys($payload)===['host','port','user','password','from','test_to']);
    $host=$payload['host']; $user=$payload['user'];
    $pass=$payload['password']; $from=$payload['from']; $testTo=$payload['test_to'];
    $port=$payload['port'];
    mail9Guard(is_string($host) && (bool)preg_match('/^[a-z0-9][a-z0-9.-]{2,198}[a-z0-9]$/Di',$host)
        && is_int($port) && in_array($port,[465,587],true));
    mail9Guard(is_string($user) && strlen($user)>=3 && strlen($user)<=254
        && is_string($pass) && strlen($pass)>=9 && strlen($pass)<=512
        && is_string($from) && filter_var($from,FILTER_VALIDATE_EMAIL)
        && is_string($testTo) && filter_var($testTo,FILTER_VALIDATE_EMAIL));
    foreach ([$host,$user,$pass,$from,$testTo] as $value) {
        mail9Guard(!preg_match('/[\r\n\x00]/',$value) && trim($value)===$value
            && !($value[0]==='"' && str_ends_with($value,'"'))
            && !($value[0]==="'" && str_ends_with($value,"'")));
    }
    $before=(string)file_get_contents($env);
    mail9Guard(strlen($before)>=200 && strlen($before)<16384);
    require $release.'/bootstrap.php';
    $currentConfig=require $release.'/config/app.php';
    mail9Guard($currentConfig['environment']==='production'
        && $currentConfig['db_name']==='u235811320_celikom'
        && $currentConfig['admin_enabled']
        && $currentConfig['auth_enabled']
        && $currentConfig['api_enabled']
        && !$currentConfig['analytics_enabled']);
    $keyList=['CELIKOM_MAIL_TRANSPORT','CELIKOM_SMTP_HOST','CELIKOM_SMTP_PORT',
        'CELIKOM_SMTP_USER','CELIKOM_SMTP_PASSWORD','CELIKOM_MAIL_FROM','CELIKOM_MAIL_CODE_PEPPER'];
    $values=['CELIKOM_MAIL_TRANSPORT'=>'smtp',
        'CELIKOM_SMTP_HOST'=>$host,'CELIKOM_SMTP_PORT'=>(string)$port,
        'CELIKOM_SMTP_USER'=>$user,'CELIKOM_SMTP_PASSWORD'=>$pass,
        'CELIKOM_MAIL_FROM'=>$from];
    $lines=explode("\n",rtrim($before,"\r\n"));
    $counts=array_fill_keys($keyList,0);
    $oldPepper='';
    foreach ($lines as $line) {
        if (preg_match('/^\s*(CELIKOM_(?:MAIL_|SMTP_)[A-Z0-9_]+)\s*=/', $line,$found)
            && !array_key_exists($found[1],$counts)) throw new RuntimeException('unknown_mail_setting');
        if (!preg_match('/^([A-Z][A-Z0-9_]*)=(.*)$/D',$line,$found)) continue;
        if (!array_key_exists($found[1],$counts)) continue;
        $counts[$found[1]]++;
        mail9Guard($counts[$found[1]]===1);
        if ($found[1]==='CELIKOM_MAIL_CODE_PEPPER') $oldPepper=$found[2];
    }
    $pepper=strlen($oldPepper)>=32 ? $oldPepper : bin2hex(random_bytes(32));
    $values['CELIKOM_MAIL_CODE_PEPPER']=$pepper;
    $present=[];
    foreach ($lines as &$line) {
        if (!preg_match('/^([A-Z][A-Z0-9_]*)=/', $line,$found)
            || !array_key_exists($found[1],$values)) continue;
        $name=$found[1];
        $line=$name.'='.$values[$name]; $present[$name]=true;
    }
    unset($line);
    foreach ($values as $name=>$value) if (!isset($present[$name])) $lines[]=$name.'='.$value;
    $next=implode("\n",$lines)."\n";
    mail9Guard(strlen($next)<20000);
    $backup=$base.'/backups/stage9-mail-env-'.gmdate('YmdTHis').'-'.bin2hex(random_bytes(8));
    mail9Guard(!file_exists($backup) && copy($env,$backup) && chmod($backup,0600));
    $switched=false; $temp=false;
    try {
        $temp=tempnam($base.'/shared','.stage9-mail-');
        mail9Guard(is_string($temp) && chmod($temp,0600)
            && file_put_contents($temp,$next,LOCK_EX)===strlen($next) && rename($temp,$env));
        $temp=false; $switched=true;
        // Test SMTP acceptance with the exact server implementation, never output the code.
        $mailerFile=dirname($source).'/SmtpMailer.php';
        mail9Guard(is_file($mailerFile) && !is_link($mailerFile));
        require_once $mailerFile;
        $mailer=new Celikom\Auth\SmtpMailer([
            'environment'=>'production','mail_transport'=>'smtp',
            'mail_host'=>$host,'mail_port'=>$port,'mail_user'=>$user,
            'mail_password'=>$pass,'mail_from'=>$from
        ]);
        mail9Guard($mailer->ready());
        $mailer->sendCode($testTo,str_pad((string)random_int(0,999999),6,'0',STR_PAD_LEFT),'verify');
        mail9Guard(hash_equals(hash('sha256',$next),hash_file('sha256',$env)));
    } catch (Throwable $error) {
        if ($switched) {
            $rollback=tempnam($base.'/shared','.stage9-mail-revert-');
            if ($rollback!==false) {
                chmod($rollback,0600);
                if (copy($backup,$rollback)) rename($rollback,$env);
                if (file_exists($rollback)) unlink($rollback);
            }
        }
        throw $error;
    } finally {
        if (is_string($temp) && is_file($temp)) unlink($temp);
    }
    echo "Stage9 private SMTP credentials provisioned with backup; TLS SMTP accepted a test email.\n";
    echo "Inbox receipt and new server release still require owner verification; no user-auth changes deployed.\n";
} catch (Throwable) {
    fwrite(STDERR,"Stage9 SMTP provisioning refused or reverted; no secrets printed.\n");
    exit(1);
}
