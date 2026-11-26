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
  expect(count($sent)===$before+1,'one reply email');expect($service->thread($id,$u)['status']==='closed','reply visible');
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
 run('Support groups accounts and bounds ticket history, closing only the answered request',function()use($service,$user,$admin,$uuid,$pdo):void{
  $u=$user();$owner=$admin('owner');$first=$service->create($u,'Первое сообщение',$uuid());$second=$service->create($u,'Новое сообщение',$uuid());
  $service->reply($owner,$first,'Ответ на первое',$uuid());
  expect($service->thread($first,$u)['status']==='closed','reply closes first');expect($service->thread($second,$u)['status']==='open','new request stays open');
  $view=new SupportAdminView($pdo);$list=$view->render(str_repeat('a',64),0);expect(substr_count($list,'account='.$u.'"')===1,'one row per account');
  $detail=$view->render(str_repeat('a',64),0,1,1,$u);expect(str_contains($detail,'Новое')&&str_contains($detail,'Закрыто'),'both statuses');
  $closed=$view->render(str_repeat('a',64),$first);expect(!str_contains($closed,'/admin/support/close')&&!str_contains($closed,'/admin/support/reply'),'closed has no action forms');
  // Older history is seeded only in the disposable DB to test page boundaries.
  for($i=0;$i<12;$i++)$pdo->prepare('INSERT INTO support_tickets(user_id,request_key) VALUES (?,?)')->execute([$u,$uuid()]);
  $page=$view->render(str_repeat('a',64),0,1,1,$u);expect(substr_count($page,'>Посмотреть</a>')===10&&str_contains($page,'page=2'),'bounded first page');
  $page=$view->render(str_repeat('a',64),0,2,1,$u);expect(substr_count($page,'>Посмотреть</a>')===4&&!str_contains($page,'page=3'),'bounded last page');
 });
 run('Support saves and responds before deferred SMTP, with no duplicate scheduling',function()use($config,$pdo,$user,$uuid):void{
  $tasks=[];$calls=0;$deferred=$config;
  $deferred['support_after_response']=static function(Closure $task)use(&$tasks):void{$tasks[]=$task;};
  $deferred['mail_test_sink']=static function($to,$body)use(&$calls):void{$calls++;expect(str_contains($body,'С уважением, команда CELIKOM'),'mail signature');expect(!str_contains($body,'Открыть переписку'),'no technical footer');};
  $s=new SupportService($pdo,$deferred);$u=$user();$key=$uuid();$id=$s->create($u,'Проверка быстрой отправки',$key);
  expect($id>0&&$calls===0&&count($tasks)===1,'committed before mail');
  $s->create($u,'Проверка быстрой отправки',$key);expect(count($tasks)===1,'retry does not schedule duplicate');
  $tasks[0]();$tasks[0]();expect($calls===1,'one mail claim');
 });
 run('Support mail failure does not lose ticket or resend ambiguous SMTP delivery',function()use($config,$pdo,$user,$uuid):void{
  $calls=0;$bad=$config;$bad['mail_test_sink']=static function()use(&$calls):void{$calls++;throw new RuntimeException('isolated_failure');};$s=new SupportService($pdo,$bad);$u=$user();$key=$uuid();$id=$s->create($u,'Почта недоступна',$key);expect($id>0,'ticket committed');$s->create($u,'Почта недоступна',$key);expect($calls===1,'no auto resend');
  expect($pdo->query('SELECT delivery FROM support_messages WHERE ticket_id='.$id)->fetchColumn()==='unknown','delivery uncertainty explicit');
 });
 run('Windows diagnostic snapshots accompany general and song cases privately, sanitized and RBAC guarded',function()use($service,$user,$admin,$uuid,$pdo):void{
  $u=$user();$owner=$admin('owner');$viewer=$admin('viewer');$key=$uuid();
  $diagnostics=['platform'=>'windows','appVersion'=>'0.24.18','nativeModuleVersion'=>'0.24.18',
    'yandexVersion'=>'5.126.1.0','integration'=>'ACTIVE','bridgeStarted'=>true,
    'enabled'=>true,'nativeMatchesApplication'=>true,'lastTrackId'=>'12345',
    'accessToken'=>'SECRET','password'=>'SECRET','email'=>'leak@example.invalid',
    'events'=>[
      ['code'=>'PLAYER_NET_HTTP_FORBIDDEN','ageSeconds'=>27,'resourceId'=>'739209',
       'url'=>'https://example.invalid?token=SECRET','authorization'=>'SECRET'],
      ['code'=>'PLAYER_URL_QUERY_CHANGED','ageSeconds'=>8,'resourceId'=>'739209'],
      ['code'=>'GARBAGE','ageSeconds'=>2,'error'=>'SECRET'],
      ['code'=>'PLAYER_NET_REQUEST','ageSeconds'=>1000,'token'=>'SECRET'],
    ]];
  $id=$service->create($u,'Периодически прерывается звук',$key,null,$diagnostics);
  expect($service->create($u,'Периодически прерывается звук',$key,null,$diagnostics)===$id,
    'same request key, same private diagnostic replays without duplicates');
  expect($service->thread($id,$u)['report']===null,
    'private general diagnostic absent from customer support thread');
  $internal=$service->thread($id);
  expect($internal['kind']==='general'&&count($internal['report']['diagnostics']['events'])===2,
    'two recent allowlisted events, ordinary reply path maintained');
  expect(!str_contains(json_encode($internal),'SECRET')&&
    !str_contains(json_encode($internal),'leak@example.invalid'),
    'server strips token, URL, arbitrary email and unsupported properties');
  $html=(new SupportAdminView($pdo))->render(str_repeat('a',64),$id);
  expect(!str_contains($html,'Техническая диагностика')&&
    str_contains($html,'Скачать диагностику JSON')&&!str_contains($html,'PLAYER_NET_HTTP_FORBIDDEN'),
    'administrator can view general report without contaminating message text');
  $email=$pdo->prepare('SELECT body FROM support_messages WHERE ticket_id=? ORDER BY id LIMIT 1');
  $email->execute([$id]);
  expect($email->fetchColumn()==='Периодически прерывается звук',
    'only clean customer text persists as mail body');
  try{$service->create($u,'Периодически прерывается звук',$key,null,
      array_replace($diagnostics,['enabled'=>false]));throw new RuntimeException('changed_payload_retry');}
  catch(InvalidArgumentException){}
  $song=['category'=>'audio_issue','track'=>['id'=>'12345','title'=>'','artist'=>'','album'=>''],
    'version'=>'0.24.18','diagnostics'=>['enabled'=>true,'bridgeReady'=>true,'windows'=>$diagnostics]];
  $songId=$service->create($u,'Проблема с песней',$uuid(),$song);
  $songReport=$service->thread($songId)['report'];
  expect(($songReport['diagnostics']['windows']['events'][0]['code']??null)==='PLAYER_NET_HTTP_FORBIDDEN',
    'song report preserves Windows event trace in existing typed song diagnostics');
  expect(!str_contains(json_encode($songReport),'SECRET'),
    'song diagnostics independently sanitized server-side');
  $panel=new AdminPanel($pdo,new LocalStorageAdapter('/tmp/celikom-support-tests'),false,false,[]);
  $auth=static function(int $adminId)use($pdo):array{
    $token=bin2hex(random_bytes(32));$csrf=AdminAuth::csrfForToken($token);
    $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES (?,?,?,UTC_TIMESTAMP()+INTERVAL 1 HOUR)')
      ->execute([hash('sha256',$token),$adminId,hash('sha256',$csrf)]);
    return ['cookie'=>AdminAuth::COOKIE.'='.$token];
  };
  $ownerAuth=$auth($owner);$viewerAuth=$auth($viewer);
  $url='/admin/support/diagnostics';$query=['ticket'=>(string)$id];
  $download=$panel->handle('GET',$url,$query,$ownerAuth,'');
  expect($download->status===200&&str_contains($download->body,'PLAYER_NET_HTTP_FORBIDDEN'),
    'private general diagnostic downloadable by owner');
  expect(!str_contains($download->body,'SECRET')&&
    str_contains($download->headers['Content-Disposition']??'','attachment'),
    'JSON remains secret-free and uses attachment policy');
  expect($panel->handle('GET',$url,$query,$viewerAuth,'')->status===403,
    'viewer prohibited from downloading user diagnostics');
  expect($panel->handle('GET',$url,$query,[],'')->status===303,
    'anonymous user requires login for diagnostic export');
  $songFile=$panel->handle('GET',$url,['ticket'=>(string)$songId],$ownerAuth,'');
  expect($songFile->status===200&&str_contains($songFile->body,'PLAYER_NET_HTTP_FORBIDDEN'),
    'song diagnostic remains downloadable');
 });
 run('Song support is separate, sanitized, deduplicated, resolvable without email and cannot close general correspondence',function()use($service,$user,$admin,$uuid,$pdo,&$sent):void{
  $u=$user();$owner=$admin('owner');$viewer=$admin('viewer');$before=count($sent);
  $report=['category'=>'audio_issue','track'=>['id'=>'50163040','artist'=>'SLIMUS','title'=>'<script>song</script>','album'=>'Album','access_token'=>'SECRET'],'version'=>'0.4.41','diagnostics'=>['phase'=>'READY','enabled'=>true,'bridgeHealthy'=>true,'replacementError'=>'api_unavailable','network'=>[['endpoint'=>'config','httpStatus'=>504,'result'=>'api_response_error','elapsedMs'=>10000,'authorization'=>'SECRET']],'token'=>'SECRET','recentLog'=>['SECRET'],'source'=>'https://private.example/SECRET']];
  $id=$service->create($u,'',$uuid(),$report);expect(count($sent)===$before,'Song report sends no email');
  expect($service->create($u,'',$uuid(),$report)===$id,'Same open song/category/comment deduplicates across request keys');
  $thread=$service->thread($id,$u);expect($thread['kind']==='song','Typed report');expect(!str_contains(json_encode($thread),'SECRET'),'Unknown diagnostic keys never stored or returned');
  $service->deliver((int)$pdo->query('SELECT id FROM support_messages WHERE ticket_id='.$id)->fetchColumn());expect(count($sent)===$before,'Song message cannot be delivered later');
  $general=$service->create($u,'Обычное сообщение',$uuid());expect(count($sent)===$before+1,'General email notification preserved');
  $view=new SupportAdminView($pdo);$account=$view->render(str_repeat('a',64),0,1,1,$u,'song');expect(str_contains($account,'Обычные обращения')&&str_contains($account,'Проблемы с песнями'),'Two account sections');expect(str_contains($account,'ticket='.$id.'"')&&!str_contains($account,'ticket='.$general.'"'),'Song list excludes general conversations');
  $all=$view->render(str_repeat('a',64),0,1,1,$u);
  expect(str_contains($all,'support_kind=all" aria-current="page"'),'All tab is active by default');
  expect(str_contains($all,'ticket='.$id.'"')&&str_contains($all,'ticket='.$general.'"'),'All includes both song and general tickets');
  expect(str_contains($all,'Проблема с песней')&&str_contains($all,'Обычное обращение'),'All labels each ticket kind');
  expect(str_contains($all,'Новых: 2 · Всего: 2'),'All counts both pending kinds');
  expect(strpos($all,'ticket='.$general.'"')<strpos($all,'ticket='.$id.'"'),'Pending All list sorts by latest ID');
  $ordinary=$view->render(str_repeat('a',64),0,1,1,$u,'general');
  expect(str_contains($ordinary,'ticket='.$general.'"')&&!str_contains($ordinary,'ticket='.$id.'"'),'General tab excludes song ticket');
  $html=$view->render(str_repeat('a',64),$id);expect(str_contains($html,'&lt;script&gt;song')&&!str_contains($html,'<script>song'),'Metadata escaped');expect(str_contains($html,'resolve-song')&&!str_contains($html,'support/reply'),'Song has resolution, no mandatory reply');expect(str_contains($html,'Скачать диагностику JSON'),'Download link available in song ticket');expect(!str_contains($html,'Техническая диагностика'),'Song inline diagnostic removed, file remains');
  $list=$view->render(str_repeat('a',64),0);
  expect(str_contains($list,'<th>Обращения</th>')&&!str_contains($list,'<th>Песни'),'Single total column');
  expect(str_contains($list,'class="support-unhandled"'),'Open account highlighted');
  $inside=$view->render(str_repeat('a',64),0,1,1,$u,'song');
  expect(str_contains($inside,'>Обычные обращения</a>')&&str_contains($inside,'>Проблемы с песнями</a>'),'Labels without counters');
  expect(str_contains($inside,'has-unhandled')&&str_contains($inside,'Новых: 1 · Всего: 1'),'Pending indicator and separate counts');
  try{$service->resolveSong($viewer,$id);throw new RuntimeException('viewer_resolved');}catch(DomainException $e){expect($e->getMessage()==='forbidden','Viewer denied');}
  try{$service->resolveSong($owner,$general);throw new RuntimeException('general_closed_without_reply');}catch(DomainException){}
  $service->resolveSong($owner,$id);$service->resolveSong($owner,$id);expect($service->thread($id,$u)['status']==='closed','Report resolved');expect($service->thread($general,$u)['status']==='open','Ordinary reply still required');expect(count($sent)===$before+1,'Resolution sends no email');
  expect((int)$pdo->query("SELECT COUNT(*) FROM audit_log WHERE entity_type='support_ticket' AND entity_id=$id AND action='support_close'")->fetchColumn()===1,'Resolution audit idempotent');
  try{\Celikom\Support\SongReport::normalize(['category'=>[]]);throw new RuntimeException('bad_report_accepted');}catch(InvalidArgumentException){}
  // New report with its own trace must not be lost in the old same-song dedupe.
  $withTrace=$report;
  $withTrace['diagnostics']['trace']=[
    ['event'=>'replacement_recovery','ageMs'=>50,'reason'=>'alignment_unstable','driftMs'=>210,'token'=>'SECRET'],
    ['event'=>'backend_http','endpoint'=>'resolve','httpCode'=>200,'elapsedMs'=>83,'authorization'=>'SECRET'],
    ['event'=>'not_whitelisted','reason'=>'ignored'],
  ];
  $second=$service->create($u,'',$uuid(),$withTrace);
  expect($second!==$id,'Repeated song problem with diagnostic trace gets separate ticket');
  $trace=$service->thread($second,$u)['report']['diagnostics']['trace'];
  expect(count($trace)===2,'Only recognized bounded events persist');
  expect(!str_contains(json_encode($trace),'SECRET'),'Trace strips private values');
  $panel=new AdminPanel($pdo,new LocalStorageAdapter('/tmp/celikom-support-tests'),false,false,[]);
  $adminCookie=static function(int $id)use($pdo):array{
   $token=bin2hex(random_bytes(32));$csrf=AdminAuth::csrfForToken($token);
   $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES (?,?,?,UTC_TIMESTAMP()+INTERVAL 1 HOUR)')->execute([hash('sha256',$token),$id,hash('sha256',$csrf)]);
   return ['cookie'=>AdminAuth::COOKIE.'='.$token];
  };
  $ownerHeaders=$adminCookie($owner);$viewerHeaders=$adminCookie($viewer);

  $open=(int)$pdo->query("SELECT COUNT(*) FROM support_tickets WHERE status='open'")->fetchColumn();
  $page=$panel->handle('GET','/admin',['tab'=>'support','account'=>(string)$u],$ownerHeaders,'');
  expect($page->status===200&&str_contains($page->body,'support_kind=all" aria-current="page"'),'Admin defaults to All');
  expect(str_contains($page->body,'>Техподдержка<span class="nav-count" aria-label="Новых: '.$open.'">'.$open.'</span>'),'Support top nav shows open ticket total');

  $url='/admin/support/diagnostics';$query=['ticket'=>(string)$second];
  $file=$panel->handle('GET',$url,$query,$ownerHeaders,'');
  expect($file->status===200&&str_contains($file->headers['Content-Disposition']??'','attachment'),'Admin downloads JSON attachment');
  $download=json_decode($file->body,true);
  expect(($download['report']['diagnostics']['trace'][0]['reason']??'')==='alignment_unstable','Downloaded file contains useful event codes');
  expect(!str_contains($file->body,'SECRET'),'Admin download contains no secret fields');
  expect($panel->handle('GET',$url,$query,[],'')->status===303,'Anonymous download requires login');
  expect($panel->handle('GET',$url,$query,$viewerHeaders,'')->status===403,'Viewer cannot download diagnostic');
  expect($panel->handle('GET',$url,['ticket'=>(string)$general],$ownerHeaders,'')->status===404,'General tickets cannot be downloaded as song diagnostics');
 });
 run('Android common support envelope is stored privately and displayed in the shared administration',function()use($service,$user,$uuid,$pdo):void{
  $u=$user();$diagnostics=['schema_version'=>1,'platform'=>'android','version'=>'0.3.52',
   'diagnostics'=>['phase'=>'ERROR','paused'=>false,'trace'=>[['event'=>'backend_http','endpoint'=>'resolve','httpCode'=>503,'authorization'=>'SECRET']]],'token'=>'SECRET'];
  $id=$service->create($u,'Проверка общего приёма Android',$uuid(),null,$diagnostics);
  expect($service->thread($id,$u)['report']===null,'Customer cannot read common mobile diagnostic attachment');
  $internal=$service->thread($id);expect($internal['report']['platform']==='android','Mobile source identified in admin attachment');
  expect(!str_contains(json_encode($internal),'SECRET'),'Mobile input independently sanitized');
  $html=(new SupportAdminView($pdo))->render(str_repeat('a',64),$id);
  expect(!str_contains($html,'Техническая диагностика')&&str_contains($html,'Скачать диагностику JSON'),'Shared admin displays mobile attachment and file link');
 });
 run('Ordinary support automatically stores a bounded attachment with admin-only download and stable retries',function()use($service,$config,$user,$admin,$uuid,$pdo,&$sent):void{
  $u=$user();$other=$user();$owner=$admin('owner');$viewer=$admin('viewer');$key=$uuid();$before=count($sent);
  $report=['schema_version'=>1,'platform'=>'chromium','version'=>'0.4.76','account'=>['email'=>'PRIVATE'],
   'diagnostics'=>['phase'=>'ERROR','currentTime'=>13.5,'activationCount'=>3,'token'=>'SECRET','source'=>'https://private/SECRET',
    'trace'=>[['event'=>'backend_http','endpoint'=>'resolve','httpCode'=>504,'elapsedMs'=>3000,'authorization'=>'SECRET']]]];
  $id=$service->create($u,'Не подключается после переключения',$key,null,$report);
  expect($service->create($u,'Не подключается после переключения',$key,null,$report)===$id,'Exact retry preserves attachment');
  expect(count($sent)===$before+1,'Ordinary mail behavior preserved without duplicate notification');
  $thread=$service->thread($id);expect($service->thread($id,$u)['report']===null,'Ordinary attachment stays private from the customer API');expect($thread['kind']==='general'&&$thread['report']['diagnostics']['currentTime']===13.5,'Ordinary request keeps snapshot even without a track');
  expect(!str_contains(json_encode($thread),'SECRET')&&!str_contains(json_encode($thread),'PRIVATE'),'Server independently strips unknown private fields');
  try{$service->thread($id,$other);throw new RuntimeException('cross_user_attachment');}catch(DomainException){}
  $html=(new SupportAdminView($pdo))->render(str_repeat('a',64),$id);
  expect(str_contains($html,'Скачать диагностику JSON')&&!str_contains($html,'Техническая диагностика')&&str_contains($html,'/admin/support/reply'),'General attachment keeps ordinary correspondence');
  $headers=static function(int $id)use($pdo):array{
   $token=bin2hex(random_bytes(32));$csrf=AdminAuth::csrfForToken($token);
   $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES (?,?,?,UTC_TIMESTAMP()+INTERVAL 1 HOUR)')->execute([hash('sha256',$token),$id,hash('sha256',$csrf)]);
   return ['cookie'=>AdminAuth::COOKIE.'='.$token];
  };
  $panel=new AdminPanel($pdo,new LocalStorageAdapter('/tmp/celikom-support-tests'),false,false,[]);
  $query=['ticket'=>(string)$id];$ownerHeaders=$headers($owner);
  $file=$panel->handle('GET','/admin/support/diagnostics',$query,$ownerHeaders,'');
  expect($file->status===200&&str_contains($file->headers['Content-Disposition'],'attachment'),'General diagnostics downloaded as file');
  expect(json_decode($file->body,true)['schema']==='celikom-support-diagnostic-v1','Explicit ordinary support schema');
  expect(!str_contains($file->body,'SECRET')&&!str_contains($file->body,'PRIVATE'),'Download sanitized');
  expect($panel->handle('GET','/admin/support/diagnostics',$query,[],'')->status===303,'Anonymous export denied');
  expect($panel->handle('GET','/admin/support/diagnostics',$query,$headers($viewer),'')->status===403,'Viewer export denied');
  $plain=$service->create($u,'Старое обращение без вложения',$uuid());
  expect($panel->handle('GET','/admin/support/diagnostics',['ticket'=>(string)$plain],$ownerHeaders,'')->status===404,'Old requests remain readable without inventing diagnostics');
  // Full HTTP request path: ordinary confirmed user, no admin rights and no trial required.
  $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES (?,UTC_TIMESTAMP(6))')->execute([$u]);
  $pdo->prepare('INSERT INTO user_devices(user_id,installation_id) VALUES (?,?)')->execute([$u,$uuid()]);$device=(int)$pdo->lastInsertId();
  $bearer=bin2hex(random_bytes(32));
  $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at) VALUES (?,?,?,?,UTC_TIMESTAMP()+INTERVAL 1 HOUR,UTC_TIMESTAMP()+INTERVAL 1 DAY)')->execute([$u,$device,hash('sha256',$bearer),hash('sha256',random_bytes(32))]);
  $app=new \Celikom\Application($config);$auth=['Authorization'=>'Bearer '.$bearer,'Content-Type'=>'application/json'];
  $payload=['kind'=>'general','message'=>'Проверка скрытой диагностики','request_key'=>$uuid(),'support_diagnostics'=>$report];
  $response=$app->handle('POST','/api/v1/support',[],$auth,json_encode($payload));expect($response->status===200,'General attachment accepted via authenticated HTTP route');
  $newId=json_decode($response->body,true)['ticket_id'];expect($service->thread($newId)['report']['diagnostics']['activationCount']===3,'HTTP route persists snapshot');
  $legacy=$app->handle('POST','/api/v1/support',[],$auth,json_encode(['kind'=>'general','message'=>'Другой прежний клиент','request_key'=>$uuid(),'report'=>['legacy'=>'unchanged'],'diagnostics'=>['platform'=>'android','legacy'=>'unchanged']]));expect($legacy->status===200,'Legacy general report field stays compatible');
  $pdo->prepare('DELETE FROM user_sessions WHERE user_id=?')->execute([$u]);$pdo->prepare('DELETE FROM user_devices WHERE user_id=?')->execute([$u]);$pdo->prepare('DELETE FROM user_email_security WHERE user_id=?')->execute([$u]);
 });
}finally{
 foreach($users as $u){$pdo->exec('DELETE m FROM support_messages m JOIN support_tickets t ON t.id=m.ticket_id WHERE t.user_id='.$u);$pdo->exec('DELETE FROM audit_log WHERE entity_type=\'support_ticket\' AND entity_id IN (SELECT id FROM support_tickets WHERE user_id='.$u.')');$pdo->exec('DELETE FROM support_tickets WHERE user_id='.$u);$pdo->exec('DELETE FROM users WHERE id='.$u);}
 foreach($admins as $a){$pdo->exec('DELETE FROM admin_sessions WHERE admin_id='.$a);$pdo->exec('DELETE FROM audit_log WHERE admin_id='.$a);$pdo->exec('DELETE FROM admins WHERE id='.$a);}
}
echo "Support inbox / retry / privacy / RBAC / CSRF / mail failure PASS\n";
