<?php
declare(strict_types=1);
// Isolated W73 contract test: disposable MySQL only, synthetic Gmail alias.
// No production DB writes, user accounts or admin sessions.
require dirname(__DIR__,3).'/server/tests/smoke.php';
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Storage\LocalStorageAdapter;
use Celikom\Admin\AdminPanel;
use Celikom\Admin\AdminAuth;
function guard73(bool $valid,string $code):void {if(!$valid)throw new RuntimeException($code);}
function uuid73():string{$x=bin2hex(random_bytes(16));return substr($x,0,8).'-'.substr($x,8,4).'-4'.substr($x,13,3).'-8'.substr($x,17,3).'-'.substr($x,20);}
$config=require dirname(__DIR__,3).'/server/config/app.php';
guard73(($config['environment']??'')==='test'&&str_starts_with((string)$config['db_name'],'celikom_test'),'disposable_only');
guard73((new Celikom\Auth\SmtpMailer($config))->ready(),'smtp_not_configured');
$from=(string)$config['mail_from'];
guard73(filter_var($from,FILTER_VALIDATE_EMAIL)!==false,'sender_email');
[$local,$domain]=explode('@',$from,2);
guard73(strlen($local)<42 && preg_match('/^[A-Za-z0-9._-]+$/D',$local)===1,'alias_guard');
$alias=$local.'+w73check'.bin2hex(random_bytes(5)).'@'.$domain;
$pdo=Connection::open($config);
(new MigrationRunner($pdo,dirname(__DIR__,3).'/server/migrations'))->run();
$uid=null;$owner=null;$viewer=null;$ticket=null;
$testOk=false;
try {
    $pdo->prepare('INSERT INTO users(email,password_hash) VALUES (?,?)')->execute([$alias,'test-fixture']);
    $uid=(int)$pdo->lastInsertId();
    $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES (?,UTC_TIMESTAMP(6))')->execute([$uid]);
    $pdo->prepare('INSERT INTO user_devices(user_id,installation_id) VALUES (?,?)')->execute([$uid,uuid73()]);
    $device=(int)$pdo->lastInsertId();
    $bearer=bin2hex(random_bytes(32));
    $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at) VALUES (?,?,?,?,UTC_TIMESTAMP()+INTERVAL 20 MINUTE,UTC_TIMESTAMP()+INTERVAL 20 MINUTE)')
       ->execute([$uid,$device,hash('sha256',$bearer),hash('sha256',random_bytes(32))]);
    $pdo->prepare("INSERT INTO admins(login,password_hash,role) VALUES (?,?,'owner')")->execute(['w73-owner-'.bin2hex(random_bytes(5)),'fixture']);
    $owner=(int)$pdo->lastInsertId();
    $pdo->prepare("INSERT INTO admins(login,password_hash,role) VALUES (?,?,'viewer')")->execute(['w73-viewer-'.bin2hex(random_bytes(5)),'fixture']);
    $viewer=(int)$pdo->lastInsertId();
    $token=bin2hex(random_bytes(32));$csrf=AdminAuth::csrfForToken($token);
    $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES (?,?,?,UTC_TIMESTAMP()+INTERVAL 1 HOUR)')
       ->execute([hash('sha256',$token),$owner,hash('sha256',$csrf)]);
    $header=['cookie'=>AdminAuth::COOKIE.'='.$token,'content-type'=>'application/x-www-form-urlencoded'];

    $config['auth_enabled']=true;
    $app=new Celikom\Application($config);
    $userAuth=['authorization'=>'Bearer '.$bearer,'content-type'=>'application/json'];
    $payload=['kind'=>'general','message'=>'W73 synthetic Windows support ticket','request_key'=>uuid73(),
      'diagnostics'=>['platform'=>'windows','appVersion'=>'0.24.20','nativeModuleVersion'=>'0.24.20',
         'integration'=>'ACTIVE','bridgeStarted'=>true,'enabled'=>true,
         'events'=>[['code'=>'ACTIVE_ENTITLEMENT_NETWORK_ERROR','ageSeconds'=>21]],
         'access_token'=>'W73_SECRET_NOT_ALLOWED']];
    $body=json_encode($payload,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
    $response=$app->handle('POST','/api/v1/support',[],$userAuth,$body);
    guard73($response->status===200,'general_api_http');
    $ticket=json_decode($response->body,true)['ticket_id']??null;
    guard73(is_int($ticket)&&$ticket>0,'ticket_id');
    $again=$app->handle('POST','/api/v1/support',[],$userAuth,$body);
    guard73($again->status===200&&(json_decode($again->body,true)['ticket_id']??null)===$ticket,'general_idempotency');

    $panel=new AdminPanel($pdo,new LocalStorageAdapter('/tmp/celikom-w73-fixture'),false,false,$config);
    $download=$panel->handle('GET','/admin/support/diagnostics',['ticket'=>(string)$ticket],$header,'');
    guard73($download->status===200&&!str_contains($download->body,'W73_SECRET_NOT_ALLOWED')
       &&(json_decode($download->body,true)['report']['platform']??null)==='windows','owner_private_json');
    guard73($panel->handle('GET','/admin/support/diagnostics',['ticket'=>(string)$ticket],[],'')->status===303,'anonymous_denied');
    guard73(($app->handle('GET','/api/v1/support/'.$ticket,[],$userAuth,'')->status)===200,'user_support_thread');
    guard73((new Celikom\Support\SupportService($pdo,$config))->thread($ticket,$uid)['report']===null,'user_report_hidden');

    $replyText='W73 synthetic admin reply for Gmail delivery';
    $form=http_build_query(['ticket'=>$ticket,'csrf'=>$csrf,'request_key'=>uuid73(),'message'=>$replyText]);
    $reply=$panel->handle('POST','/admin/support/reply',[],$header,$form);
    guard73($reply->status===303,'admin_reply_submit');
    guard73($panel->handle('POST','/admin/support/reply',[],$header,$form)->status===303,'admin_reply_idempotent');
    $q=$pdo->prepare('SELECT admin_id,delivery,mail_required FROM support_messages WHERE ticket_id=? ORDER BY id');$q->execute([$ticket]);
    $messages=$q->fetchAll(PDO::FETCH_ASSOC);
    guard73(count($messages)===2 && $messages[0]['admin_id']===null && $messages[1]['admin_id']!==null
      &&$messages[0]['delivery']==='sent'&&$messages[1]['delivery']==='sent'
      &&(int)$messages[0]['mail_required']===1&&(int)$messages[1]['mail_required']===1,'both_smtp_required_sent');

    $song=['kind'=>'song','message'=>'W73 song fixture','request_key'=>uuid73(),
       'report'=>['category'=>'audio_issue','version'=>'0.24.20',
       'track'=>['id'=>'50163040','title'=>'','artist'=>'','album'=>''],
       'diagnostics'=>['enabled'=>true,'bridgeReady'=>true,'windows'=>['platform'=>'windows','appVersion'=>'0.24.20','enabled'=>true,'events'=>[]]]]];
    $s=$app->handle('POST','/api/v1/support',[],$userAuth,json_encode($song,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE));
    guard73($s->status===200,'song_api');
    $songId=json_decode($s->body,true)['ticket_id'];
    $q=$pdo->prepare('SELECT mail_required FROM support_messages WHERE ticket_id=?');$q->execute([$songId]);
    guard73((int)$q->fetchColumn()===0,'song_mail_disabled');
    $output=getenv('W73_RESULT_FILE');
    guard73(is_string($output)&&str_starts_with($output,'/tmp/')&&!is_link($output),'result_guard');
    guard73(file_put_contents($output,json_encode(['ticket'=>$ticket,'alias'=>$alias,'support_from'=>$from],JSON_THROW_ON_ERROR),LOCK_EX)!==false,'result_file');
    chmod($output,0600);
    echo "W73_DISPOSABLE_WINDOWS_GENERAL_ADMIN_REPLY_SMTP_SENT_SONG_RBAC_PASS\n";
    $testOk=true;
}finally {
    // MySQL service is disposable; delete test identities explicitly anyway.
    if($uid!==null){
        $pdo->prepare("DELETE FROM audit_log WHERE entity_type='support_ticket' AND entity_id IN (SELECT id FROM support_tickets WHERE user_id=?)")->execute([$uid]);
        $pdo->prepare('DELETE m FROM support_messages m JOIN support_tickets t ON t.id=m.ticket_id WHERE t.user_id=?')->execute([$uid]);
        $pdo->prepare('DELETE FROM support_tickets WHERE user_id=?')->execute([$uid]);
        $pdo->prepare('DELETE FROM user_sessions WHERE user_id=?')->execute([$uid]);
        $pdo->prepare('DELETE FROM user_devices WHERE user_id=?')->execute([$uid]);
        $pdo->prepare('DELETE FROM user_email_security WHERE user_id=?')->execute([$uid]);
        $pdo->prepare('DELETE FROM users WHERE id=?')->execute([$uid]);
    }
    foreach([$owner,$viewer] as $id)if($id!==null){
        $pdo->prepare('DELETE FROM admin_sessions WHERE admin_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM audit_log WHERE admin_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM admins WHERE id=?')->execute([$id]);
    }
}
guard73($testOk,'incomplete');
