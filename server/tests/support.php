<?php
declare(strict_types=1);
require __DIR__.'/smoke.php';
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Support\SupportService;
use Celikom\Support\SupportAdminView;
use Celikom\Admin\AdminPanel;
use Celikom\Admin\AdminAuth;
use Celikom\Storage\LocalStorageAdapter;
$config=require dirname(__DIR__).'/config/app.php';
if(!str_starts_with($config['db_name'],'celikom_test'))throw new RuntimeException('disposable_support_only');
$pdo=Connection::open($config);(new MigrationRunner($pdo,dirname(__DIR__).'/migrations'))->run();
$users=[];$admins=[];$sent=[];
$uuid=static function():string{$h=bin2hex(random_bytes(16));return substr($h,0,8).'-'.substr($h,8,4).'-4'.substr($h,13,3).'-8'.substr($h,17,3).'-'.substr($h,20);};
$user=static function()use($pdo,&$users):int{$pdo->prepare('INSERT INTO users(email,password_hash) VALUES (?,?)')->execute(['support-'.bin2hex(random_bytes(8)).'@example.invalid','fixture']);$id=(int)$pdo->lastInsertId();$users[]=$id;return $id;};
$admin=static function(string $role)use($pdo,&$admins):int{$pdo->prepare('INSERT INTO admins(login,password_hash,role) VALUES (?,?,?)')->execute(['support-'.bin2hex(random_bytes(8)),'fixture',$role]);$id=(int)$pdo->lastInsertId();$admins[]=$id;return $id;};
$config['environment']='test';$config['mail_from']='support@example.invalid';$config['mail_test_sink']=static function($to,$message,$purpose)use(&$sent):void{$sent[]=[$to,$message,$purpose];};
$service=new SupportService($pdo,$config);
$config['auth_enabled']=true;
run('Support API requires customer session',function()use($config):void{expect((new \Celikom\Application($config))->handle('GET','/api/v1/support')->status===401,'anonymous inbox forbidden');});
try{
 run('Support inbox persists, retries once, isolates account and limits volume atomically',function()use($service,$user,$uuid,&$sent,$pdo):void{
  $u=$user();$other=$user();$key=$uuid();$id=$service->create($u,'Не воспроизводится песня',$key);
  expect($service->create($u,'Не воспроизводится песня',$key)===$id,'replay returns original');expect(count($sent)===1,'one notification');expect($sent[0][0]==='support@example.invalid','configured OTP sender receives copy');
  try{$service->create($u,'Другое сообщение',$key);throw new RuntimeException('changed_replay_accepted');}catch(InvalidArgumentException){}
  expect(count($service->listForUser($other))===0,'other inbox empty');
  try{$service->thread($id,$other);throw new RuntimeException('cross_account_read');}catch(DomainException $e){expect($e->getMessage()==='not_found','conceal ticket');}
  for($i=0;$i<4;$i++)$service->create($u,'Ещё одно обращение '.$i,$uuid());
  try{$service->create($u,'Шестое обращение',$uuid());throw new RuntimeException('rate_limit_missing');}catch(DomainException $e){expect($e->getMessage()==='rate_limited','hourly cap');}
  expect((int)$pdo->query('SELECT COUNT(*) FROM support_tickets WHERE user_id='.$u)->fetchColumn()===5,'no partial sixth ticket');
 });
 run('Support admin reply is idempotent, escaped, audited and cannot be sent by viewer',function()use($service,$user,$admin,$uuid,$pdo,&$sent):void{
  $u=$user();$owner=$admin('owner');$viewer=$admin('viewer');$id=$service->create($u,'Тестовое обращение',$uuid());$key=$uuid();$before=count($sent);
  try{$service->reply($viewer,$id,'Ответ наблюдателя',$key);throw new RuntimeException('viewer_reply');}catch(DomainException $e){expect($e->getMessage()==='forbidden','viewer forbidden');}
  $service->reply($owner,$id,'Ответ <script>alert(1)</script>',$key);$service->reply($owner,$id,'Ответ <script>alert(1)</script>',$key);
  expect(count($sent)===$before+1,'one reply email');expect($service->thread($id,$u)['status']==='answered','reply visible');
  expect((int)$pdo->query("SELECT COUNT(*) FROM audit_log WHERE entity_type='support_ticket' AND entity_id=$id AND action='support_reply'")->fetchColumn()===1,'one audit');
  $html=(new SupportAdminView($pdo))->render(str_repeat('a',64),$id);expect(str_contains($html,'&lt;script&gt;')&&!str_contains($html,'<script>alert'),'stored HTML escaped');
  $token=bin2hex(random_bytes(32));$csrf=AdminAuth::csrfForToken($token);$pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES (?,?,?,UTC_TIMESTAMP()+INTERVAL 1 HOUR)')->execute([hash('sha256',$token),$owner,hash('sha256',$csrf)]);
  $panel=new AdminPanel($pdo,new LocalStorageAdapter('/tmp/celikom-support-tests'),false,false,[]);
  $headers=['cookie'=>AdminAuth::COOKIE.'='.$token,'content-type'=>'application/x-www-form-urlencoded'];
  expect($panel->handle('POST','/admin/support/reply',[],$headers,http_build_query(['ticket'=>$id,'message'=>'Ответ без CSRF','request_key'=>$uuid()]))->status===403,'CSRF enforced');
  for($i=0;$i<5;$i++)$service->reply($owner,$id,'Дополнительный ответ '.$i,$uuid());
  expect($service->thread($id,$u)['has_more'],'message history paginated');expect($service->thread($id,$u,2)['messages'][0]['author']==='user','original request remains available');
  $service->close($owner,$id);expect($service->thread($id,$u)['status']==='closed','closed status');
 });
 run('Support mail failure does not lose ticket or resend ambiguous SMTP delivery',function()use($config,$pdo,$user,$uuid):void{
  $calls=0;$bad=$config;$bad['mail_test_sink']=static function()use(&$calls):void{$calls++;throw new RuntimeException('isolated_failure');};$s=new SupportService($pdo,$bad);$u=$user();$key=$uuid();$id=$s->create($u,'Почта недоступна',$key);expect($id>0,'ticket committed');$s->create($u,'Почта недоступна',$key);expect($calls===1,'no auto resend');
  expect($pdo->query('SELECT delivery FROM support_messages WHERE ticket_id='.$id)->fetchColumn()==='unknown','delivery uncertainty explicit');
 });
}finally{
 foreach($users as $u){$pdo->exec('DELETE m FROM support_messages m JOIN support_tickets t ON t.id=m.ticket_id WHERE t.user_id='.$u);$pdo->exec('DELETE FROM audit_log WHERE entity_type=\'support_ticket\' AND entity_id IN (SELECT id FROM support_tickets WHERE user_id='.$u.')');$pdo->exec('DELETE FROM support_tickets WHERE user_id='.$u);$pdo->exec('DELETE FROM users WHERE id='.$u);}
 foreach($admins as $a){$pdo->exec('DELETE FROM admin_sessions WHERE admin_id='.$a);$pdo->exec('DELETE FROM audit_log WHERE admin_id='.$a);$pdo->exec('DELETE FROM admins WHERE id='.$a);}
}
echo "Support inbox / retry / privacy / RBAC / CSRF / mail failure PASS\n";
