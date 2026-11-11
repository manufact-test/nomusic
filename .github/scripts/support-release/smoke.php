<?php
declare(strict_types=1);
// Live QA uses a disposable customer only. No real emails, account edits or new admin roles.
ini_set('display_errors','0');
function supportCheck(bool $ok,string $code):void {if(!$ok)throw new RuntimeException($code);}
function supportHttp(string $path,string $method='GET',?string $body=null,string $bearer='',string $cookie='',string $origin='https://music.yandex.ru'):array {
 supportCheck(str_starts_with($path,'/api/v1/')||str_starts_with($path,'/admin/support/')||str_starts_with($path,'/admin?tab=support&ticket='),'http_path');
 $ch=curl_init('https://darkred-camel-588676.hostingersite.com'.$path);$headers=[];
 $request=['Origin: '.$origin,'Cache-Control: no-store'];
 if($body!==null)$request[]='Content-Type: application/json';
 if($bearer!=='')$request[]='Authorization: Bearer '.$bearer;
 if($cookie!=='')$request[]='Cookie: '.$cookie;
 curl_setopt_array($ch,[CURLOPT_CUSTOMREQUEST=>$method,CURLOPT_RETURNTRANSFER=>true,CURLOPT_HTTPHEADER=>$request,
  CURLOPT_FOLLOWLOCATION=>false,CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,
  CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>20,CURLOPT_HEADERFUNCTION=>static function($handle,string $line)use(&$headers):int{
   if(str_contains($line,':')){[$key,$value]=explode(':',$line,2);$headers[strtolower(trim($key))]=trim($value);}return strlen($line);
  }]);
 if($body!==null)curl_setopt($ch,CURLOPT_POSTFIELDS,$body);
 $text=curl_exec($ch);$code=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);curl_close($ch);
 supportCheck(is_string($text)&&strlen($text)<65536&&$code>0,'http_transport');
 return [$code,$text,$headers];
}
$pdo=null;$uid=null;$email=null;$adminHash=null;$success=false;
try {
 supportCheck(PHP_SAPI==='cli'&&$argc===2,'arguments');
 $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
 $release=realpath($root.'/current');
 supportCheck($release===$root.'/releases/'.$argv[1]&&preg_match('/^browser-support-076-[a-f0-9]{12}$/D',$argv[1])===1,'active_release');
 require $release.'/bootstrap.php';$config=require $release.'/config/app.php';
 supportCheck($config['db_name']==='u235811320_celikom'&&$config['auth_enabled']&&$config['admin_enabled'],'site_config');
 supportCheck(function_exists('curl_init'),'curl_required');
 $health=supportHttp('/api/v1/config');supportCheck($health[0]===200,'public_config');
 supportCheck(supportHttp('/api/v1/resolve?service=yandex&track_id=1')[0]===401,'anonymous_resolve');
 $cors=supportHttp('/api/v1/audio/1','OPTIONS',null,'','','music-application://desktop');
 supportCheck($cors[0]===204&&($cors[2]['access-control-allow-origin']??null)==='music-application://desktop','native_audio_cors');
 $authCors=supportHttp('/api/v1/auth/me','OPTIONS',null,'','','music-application://desktop');
 supportCheck(!isset($authCors[2]['access-control-allow-origin']),'account_cors_closed');
 $pdo=Celikom\Database\Connection::open($config);
 $owner=$pdo->query("SELECT id FROM admins WHERE role='owner' AND enabled=1 ORDER BY id LIMIT 1")->fetchColumn();
 supportCheck($owner!==false,'existing_owner');
 $email='support-release-'.bin2hex(random_bytes(16)).'@example.invalid';
 $pdo->prepare('INSERT INTO users(email,password_hash) VALUES (?,?)')->execute([$email,password_hash(bin2hex(random_bytes(32)),PASSWORD_BCRYPT,['cost'=>10])]);
 $uid=(int)$pdo->lastInsertId();
 $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES (?,UTC_TIMESTAMP(6))')->execute([$uid]);
 $uuid=static function():string{$h=bin2hex(random_bytes(16));return substr($h,0,8).'-'.substr($h,8,4).'-4'.substr($h,13,3).'-8'.substr($h,17,3).'-'.substr($h,20);};
 $pdo->prepare('INSERT INTO user_devices(user_id,installation_id) VALUES (?,?)')->execute([$uid,$uuid()]);$device=(int)$pdo->lastInsertId();
 $bearer=bin2hex(random_bytes(32));
 $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at) VALUES (?,?,?,?,UTC_TIMESTAMP()+INTERVAL 5 MINUTE,UTC_TIMESTAMP()+INTERVAL 5 MINUTE)')
  ->execute([$uid,$device,hash('sha256',$bearer),hash('sha256',random_bytes(32))]);
 $adminToken=bin2hex(random_bytes(32));$adminHash=hash('sha256',$adminToken);
 $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES (?,?,?,UTC_TIMESTAMP()+INTERVAL 5 MINUTE)')
  ->execute([$adminHash,(int)$owner,hash('sha256',Celikom\Admin\AdminAuth::csrfForToken($adminToken))]);
 // Initial creation exercises the active Application against its live database,
 // but captures the deferred notification and never sends any mail. HTTPS then
 // replays the exact persisted request, which must not schedule a second delivery.
 $config['mail_transport']='disabled';
 $tasks=[];$config['support_after_response']=static function(Closure $task)use(&$tasks):void{$tasks[]=$task;};
 $config['mail_test_sink']=static function():void{throw new RuntimeException('qa_mail_forbidden');};
 $app=new Celikom\Application($config);
 $payload=['kind'=>'general','message'=>'Проверка автоматического вложения поддержки','request_key'=>$uuid(),
  'support_diagnostics'=>['schema_version'=>1,'platform'=>'chromium','version'=>'0.4.76',
   'diagnostics'=>['phase'=>'ERROR','currentTime'=>12.5,'enabled'=>true,
    'trace'=>[['event'=>'backend_http','endpoint'=>'resolve','httpCode'=>504,'elapsedMs'=>1200,'authorization'=>'QA_PRIVATE_MARKER']],
    'access_token'=>'QA_PRIVATE_MARKER','url'=>'https://example.invalid/QA_PRIVATE_MARKER']]];
 $body=json_encode($payload,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
 $saved=$app->handle('POST','/api/v1/support',[],['authorization'=>'Bearer '.$bearer,'content-type'=>'application/json'],$body);
 supportCheck($saved->status===200&&count($tasks)===1,'live_persistence');
 $ticket=json_decode($saved->body,true,8,JSON_THROW_ON_ERROR)['ticket_id']??null;
 supportCheck(is_int($ticket)&&$ticket>0,'ticket_created');
 $pdo->prepare('UPDATE support_messages SET mail_required=0 WHERE ticket_id=?')->execute([$ticket]);
 $replayed=false;
 for($attempt=0;$attempt<10;$attempt++){
  $repeat=supportHttp('/api/v1/support','POST',$body,$bearer);
  if($repeat[0]===200&&(json_decode($repeat[1],true)['ticket_id']??null)===$ticket){$replayed=true;break;}
  $error=json_decode($repeat[1],true)['error']??'non_json';
  if(!is_string($error)||!preg_match('/^[a-z_]{1,64}$/D',$error))$error='other';
  echo 'SUPPORT_HTTPS_RETRY_STATUS:'.$repeat[0].':'.$error."\n";
  usleep(1000000);
 }
 supportCheck($replayed,'https_exact_retry');
 $q=$pdo->prepare('SELECT COUNT(*) FROM support_tickets WHERE user_id=?');$q->execute([$uid]);supportCheck((int)$q->fetchColumn()===1,'no_duplicate_ticket');
 $customer=supportHttp('/api/v1/support/'.$ticket,'GET',null,$bearer);
 supportCheck($customer[0]===200&&(json_decode($customer[1],true)['report']??null)===null,'customer_report_hidden');
 $downloadPath='/admin/support/diagnostics?ticket='.$ticket;
 $file=supportHttp($downloadPath,'GET',null,'',Celikom\Admin\AdminAuth::COOKIE.'='.$adminToken);
 supportCheck($file[0]===200&&str_contains($file[2]['content-disposition']??'','attachment')
  &&($file[2]['cache-control']??'')==='no-store'&&($file[2]['x-content-type-options']??'')==='nosniff','admin_attachment');
 $attachment=json_decode($file[1],true,16,JSON_THROW_ON_ERROR);
 supportCheck(($attachment['report']['platform']??null)==='chromium'
  &&($attachment['report']['diagnostics']['currentTime']??null)===12.5
  &&!str_contains($file[1],'QA_PRIVATE_MARKER'),'attachment_sanitized');
 supportCheck(supportHttp($downloadPath)[0]===303&&supportHttp($downloadPath,'GET',null,$bearer)[0]===303,'customer_export_denied');
 $page=supportHttp('/admin?tab=support&ticket='.$ticket,'GET',null,'',Celikom\Admin\AdminAuth::COOKIE.'='.$adminToken);
 supportCheck($page[0]===200&&str_contains($page[1],'Скачать диагностику JSON')&&str_contains($page[1],'Техническая диагностика расширения')&&!str_contains($page[1],'QA_PRIVATE_MARKER'),'admin_page');
 foreach(['android','windows'] as $platform){
  $other=$payload;$other['request_key']=$uuid();$other['message']='Проверка общего приёма диагностики';
  if($platform==='android')$other['support_diagnostics']['platform']='android';
  else {unset($other['support_diagnostics']);$other['diagnostics']=['platform'=>'windows','appVersion'=>'0.24.18',
   'enabled'=>true,'events'=>[['code'=>'PLAYER_NET_HTTP_FORBIDDEN','ageSeconds'=>1,'authorization'=>'QA_PRIVATE_MARKER']]];}
  $otherBody=json_encode($other,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE);
  $stored=$app->handle('POST','/api/v1/support',[],['authorization'=>'Bearer '.$bearer,'content-type'=>'application/json'],$otherBody);
  supportCheck($stored->status===200,'cross_platform_persistence');
  $otherId=json_decode($stored->body,true)['ticket_id']??null;supportCheck(is_int($otherId),'cross_platform_ticket');
  $pdo->prepare('UPDATE support_messages SET mail_required=0 WHERE ticket_id=?')->execute([$otherId]);
  $again=supportHttp('/api/v1/support','POST',$otherBody,$bearer);supportCheck($again[0]===200&&(json_decode($again[1],true)['ticket_id']??null)===$otherId,'cross_platform_https_retry');
  $otherPage=supportHttp('/admin?tab=support&ticket='.$otherId,'GET',null,'',Celikom\Admin\AdminAuth::COOKIE.'='.$adminToken);
  supportCheck($otherPage[0]===200&&str_contains($otherPage[1],'Скачать диагностику JSON')&&str_contains($otherPage[1],$platform==='android'?'Техническая диагностика Android':'Техническая диагностика Windows'),'cross_platform_admin_page');
  $otherFile=supportHttp('/admin/support/diagnostics?ticket='.$otherId,'GET',null,'',Celikom\Admin\AdminAuth::COOKIE.'='.$adminToken);
  supportCheck($otherFile[0]===200&&(json_decode($otherFile[1],true)['report']['platform']??null)===$platform&&!str_contains($otherFile[1],'QA_PRIVATE_MARKER'),'cross_platform_download');
 }
 $q=$pdo->prepare('SELECT COUNT(*) FROM account_trials WHERE user_id=?');$q->execute([$uid]);supportCheck((int)$q->fetchColumn()===0,'no_trial_activation');
 $success=true;
}catch(Throwable $error){
 $code=$error instanceof RuntimeException&&preg_match('/^[a-z_]{1,64}$/D',$error->getMessage())?$error->getMessage():'unexpected';
 fwrite(STDERR,'SUPPORT_LIVE_CHECK_FAILED:'.$code."\n");
}finally{
 if($pdo instanceof PDO){
  try {
   if($pdo->inTransaction())$pdo->rollBack();$pdo->beginTransaction();
   if($uid!==null&&$email!==null){
    $q=$pdo->prepare('SELECT email FROM users WHERE id=? FOR UPDATE');$q->execute([$uid]);supportCheck($q->fetchColumn()===$email,'qa_cleanup_identity');
    $pdo->prepare('DELETE m FROM support_messages m JOIN support_tickets t ON t.id=m.ticket_id WHERE t.user_id=?')->execute([$uid]);
    $pdo->prepare('DELETE FROM support_tickets WHERE user_id=?')->execute([$uid]);
    $pdo->prepare('DELETE FROM user_sessions WHERE user_id=?')->execute([$uid]);
    $pdo->prepare('DELETE FROM user_devices WHERE user_id=?')->execute([$uid]);
    $pdo->prepare('DELETE FROM user_email_security WHERE user_id=?')->execute([$uid]);
    $pdo->prepare('DELETE FROM users WHERE id=? AND email=?')->execute([$uid,$email]);
   }
   if($adminHash!==null)$pdo->prepare('DELETE FROM admin_sessions WHERE token_hash=?')->execute([$adminHash]);
   $pdo->commit();
  }catch(Throwable $cleanup){if($pdo->inTransaction())$pdo->rollBack();$success=false;fwrite(STDERR,"SUPPORT_QA_CLEANUP_FAILED\n");}
 }
}
if(!$success)exit(1);
echo "SUPPORT_LIVE_PASS: saved Chrome/Android-envelope/Windows-envelope; HTTPS retry; no duplicates; protected JSON download; secrets removed; customer denied; no trial; QA removed; no emails\n";
