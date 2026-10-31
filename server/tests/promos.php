<?php

declare(strict_types=1);
require __DIR__.'/smoke.php';
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Promo\PromoService;
use Celikom\Promo\PromoAccessService;
use Celikom\Entitlement\EntitlementService;
use Celikom\Entitlement\TrialService;
use Celikom\Incident\IncidentService;
$config=require dirname(__DIR__).'/config/app.php';
if(!str_starts_with($config['db_name'],'celikom_test'))throw new RuntimeException('disposable_promos_only');
$pdo=Connection::open($config);(new MigrationRunner($pdo,dirname(__DIR__).'/migrations'))->run();
$pdo->prepare("INSERT INTO admins(login,password_hash,role) VALUES (?,?,'owner')")->execute(['promo-'.bin2hex(random_bytes(8)),'fixture']);$owner=(int)$pdo->lastInsertId();
$users=[];$codes=[];$service=new PromoService($pdo);$now=(int)$pdo->query('SELECT UNIX_TIMESTAMP(UTC_TIMESTAMP())')->fetchColumn();
$clock=static function(int $s)use($pdo,$now):void{$pdo->exec('SET timestamp='.($now+$s));};
$user=static function()use($pdo,&$users):int{$pdo->prepare('INSERT INTO users(email,password_hash) VALUES (?,?)')->execute(['promo-'.bin2hex(random_bytes(8)).'@example.invalid','fixture']);$id=(int)$pdo->lastInsertId();$users[]=$id;$pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES (?,UTC_TIMESTAMP(6))')->execute([$id]);return $id;};
$create=static function(array $more=[])use($service,$owner,&$codes):array{$input=$more+['code'=>'PROMO_'.bin2hex(random_bytes(8)),'title'=>'Fixture','discount_percent'=>100,'duration_days'=>30,'max_activations'=>1,'activation_window'=>'unlimited','request_key'=>bin2hex(random_bytes(32))];$id=$service->create($owner,$input);$codes[]=$id;return [$id,strtoupper($input['code'])];};
try{
 $clock(0);
 run('Promo finite stacking, replay and individual revoke preserve original trial',function()use($pdo,$user,$create,$service,$owner):void{
  $id=$user();(new TrialService($pdo))->activate($id);$base=(new EntitlementService($pdo))->check($id)->validUntil;
  [$codeId,$code]=$create();$r=$service->redeem($id,$code);
  expect($r['entitlement']['allowed']&&$r['entitlement']['source']==='promo','free access');
  expect(IncidentService::micros($r['entitlement']['valid_until'])-IncidentService::micros($base)===30*86400000000,'30 days added to remainder');
  expect($service->redeem($id,$code)['already_activated'],'retry idempotent');
  expect((int)$pdo->query('SELECT used_activations FROM promo_codes WHERE id='.$codeId)->fetchColumn()===1,'one use');
  $service->revokeRedemption($owner,$r['redemption_id']);$service->revokeRedemption($owner,$r['redemption_id']);
  expect((new EntitlementService($pdo))->check($id)->validUntil===$base,'original trial retained');
  expect($service->redeem($id,$code)['revoked'],'revoked cannot reactivate');
 });
 run('Promo lifetime requires explicit confirmation and can be revoked',function()use($pdo,$user,$create,$service,$owner):void{
  try{$create(['forever'=>'1']);throw new RuntimeException('confirmation_missing');}catch(InvalidArgumentException $e){expect($e->getMessage()==='confirm_forever_required','confirmation required');}
  [$codeId,$code]=$create(['forever'=>'1','confirm_forever'=>'1']);$id=$user();$r=$service->redeem($id,$code);
  expect($r['entitlement']['allowed']&&$r['entitlement']['valid_until']===null,'forever');
  expect((int)$pdo->query('SELECT COUNT(*) FROM account_trials WHERE user_id='.$id)->fetchColumn()===0,'redemption does not start trial');
  $service->revokeRedemption($owner,$r['redemption_id']);expect(!(new EntitlementService($pdo))->check($id)->allowed,'revocation enforced');
  expect((new TrialService($pdo))->activate($id)['activated'],'first Start retains existing trial behavior');
 });
 run('Promo cap applies across accounts and partial discount is not free time',function()use($pdo,$user,$create,$service):void{
  [$codeId,$code]=$create();$service->redeem($user(),$code);
  try{$service->redeem($user(),$code);throw new RuntimeException('cap_missing');}catch(DomainException $e){expect($e->getMessage()==='promo_unavailable','cap enforced');}
  [$partial,$discount]=$create(['discount_percent'=>20]);
  try{$service->redeem($user(),$discount);throw new RuntimeException('payment_missing');}catch(DomainException $e){expect($e->getMessage()==='promo_payment_pending','discount deferred');}
  expect((int)$pdo->query('SELECT used_activations FROM promo_codes WHERE id='.$partial)->fetchColumn()===0,'no use without payment');
 });
 run('Admin lifetime confirmation does not create a code; activation view and CSRF are enforced',function()use($pdo,$config,$owner,$user,$create,$service,&$codes):void{
  $token=bin2hex(random_bytes(32));$csrf=hash_hmac('sha256','celikom-admin-csrf-v1',$token);
  $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES (?,?,?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 6 HOUR))')->execute([hash('sha256',$token),$owner,hash('sha256',$csrf)]);
  $panel=new Celikom\Admin\AdminPanel($pdo,new Celikom\Storage\LocalStorageAdapter($config['storage_path']));
  $headers=['cookie'=>Celikom\Admin\AdminAuth::COOKIE.'='.$token,'content-type'=>'application/x-www-form-urlencoded'];
  $form=['csrf'=>$csrf,'code'=>'FOREVER_'.bin2hex(random_bytes(6)),'title'=>'<fixture>','discount_percent'=>'100','forever'=>'1','max_activations'=>'1','activation_window'=>'unlimited','request_key'=>bin2hex(random_bytes(32))];
  $before=(int)$pdo->query('SELECT COUNT(*) FROM promo_codes')->fetchColumn();$response=$panel->handle('POST','/admin/promos/create',[],$headers,http_build_query($form));
  expect($response->status===200&&str_contains($response->body,'Точно хотите выдать доступ навсегда?'),'separate confirmation');
  expect((int)$pdo->query('SELECT COUNT(*) FROM promo_codes')->fetchColumn()===$before,'no code on first submit');
  expect(!str_contains($response->body,'value="<fixture>"'),'confirmation escaped');
  expect($panel->handle('POST','/admin/promos/revoke-activation',[],$headers,'id=1')->status===403,'csrf required');
  [$cid,$code]=$create();$id=$user();$r=$service->redeem($id,$code);
  $unseen=(int)$pdo->query('SELECT COUNT(*) FROM promo_redemptions')->fetchColumn();
  $beforeActivations=$panel->handle('GET','/admin',['tab'=>'promos'],$headers,'');
  expect(str_contains($beforeActivations->body,'>Промокоды<span class="nav-count" aria-label="Новых: '.$unseen.'">'.$unseen.'</span>'),'New promo activations are counted in top navigation');
  $viewNew=$panel->handle('GET','/admin/promos/new',[],$headers,'');
  expect(str_contains($viewNew->body,'>Промокоды<span class="nav-count"'),'Code creation view does not clear activation notice');
  $response=$panel->handle('GET','/admin',['tab'=>'promos','activations'=>'1'],$headers,'');
  expect($response->status===200&&str_contains($response->body,$code)&&str_contains($response->body,'/admin/promos/revoke-activation'),'activation and revoke rendered');
  $afterActivations=$panel->handle('GET','/admin',['tab'=>'promos'],$headers,'');
  expect(!str_contains($afterActivations->body,'>Промокоды<span class="nav-count"'),'Opening Activations clears per-admin promo notice');
  [$nextId,$nextCode]=$create();$nextUser=$user();$service->redeem($nextUser,$nextCode);
  $newActivation=$panel->handle('GET','/admin',['tab'=>'promos'],$headers,'');
  expect(str_contains($newActivation->body,'>Промокоды<span class="nav-count" aria-label="Новых: 1">1</span>'),'New promo activation reappears after being reviewed');

  foreach(['/admin/promos','/admin/promos/new','/admin/promos/activations'] as $route){
   $page=$panel->handle('GET',$route,[],$headers,'');expect($page->status===200,'promo path loads');
   if($route==='/admin/promos/new'){expect(str_contains($page->body,'name="request_key"')&&!str_contains($page->body,'<table>'),'creation isolated from lists');expect(str_contains($page->body,'data-promo-deadline hidden')&&str_contains($page->body,'московское время')&&!str_contains($page->body,'Дни добавляются'),'conditional deadline, Moscow and removed paragraph');expect(str_contains($page->headers['Content-Security-Policy'],"script-src 'sha256-"),'form script CSP hash');$fixture=tempnam(sys_get_temp_dir(),'promo-form-');file_put_contents($fixture,$page->body);try{passthru('node '.escapeshellarg(__DIR__.'/promo-form-browser.mjs').' '.escapeshellarg($fixture),$exit);expect($exit===0,'native promo form desktop/mobile');}finally{unlink($fixture);}}
   else {expect(str_contains($page->body,'class="promo-subnav"')&&str_contains($page->body,'aria-current="page"'),'selected submenu visible');$fixture=tempnam(sys_get_temp_dir(),'promo-table-');file_put_contents($fixture,$page->body);try{passthru('node '.escapeshellarg(__DIR__.'/promo-form-browser.mjs').' '.escapeshellarg($fixture),$exit);expect($exit===0,'native promo table layout');}finally{unlink($fixture);}}
  }
  foreach([false,true] as $forever){
   $submitted=$form;$submitted['code']='CREATE_'.strtoupper(bin2hex(random_bytes(6)));$submitted['request_key']=bin2hex(random_bytes(32));
   $submitted['forever']=$forever?'1':'0';$submitted['confirm_forever']='1';$submitted['duration_days']='30';
   $saved=$panel->handle('POST','/admin/promos/create',[],$headers,http_build_query($submitted));
   expect($saved->status===303&&$saved->headers['Location']==='/admin/promos','form saves and returns to codes');
   $q=$pdo->prepare('SELECT id,forever FROM promo_codes WHERE request_key=?');$q->execute([$submitted['request_key']]);$savedRow=$q->fetch(PDO::FETCH_ASSOC);
   expect($savedRow!==false&&(int)$savedRow['forever']===($forever?1:0),'submitted finite/lifetime code exists');$codes[]=(int)$savedRow['id'];
  }
  $pdo->exec('DELETE FROM admin_sessions WHERE admin_id='.$owner);
 });
 run('Moscow deadline converts to UTC and expires at the exact instant',function()use($pdo,$user,$create,$service,$clock,$now):void{
  $clock(0);$instant=$now+86400;
  $local=(new DateTimeImmutable('@'.$instant))->setTimezone(new DateTimeZone('Europe/Moscow'))->format('Y-m-d\TH:i');
  [$cid,$code]=$create(['activation_window'=>'fixed','activation_deadline'=>$local,'max_activations'=>2]);
  $stored=$pdo->query('SELECT activation_deadline FROM promo_codes WHERE id='.$cid)->fetchColumn();
  $expected=(new DateTimeImmutable($local,new DateTimeZone('Europe/Moscow')))->setTimezone(new DateTimeZone('UTC'))->format('Y-m-d H:i:s.000000');
  expect($stored===$expected,'Moscow input stored as UTC without shifting duration');
  expect(Celikom\Support\MoscowTime::display('2026-10-31 21:00:00')==='01.11.2026 00:00','Moscow day rollover');
  expect(Celikom\Support\MoscowTime::utc(new DateTimeImmutable('2026-11-01',new DateTimeZone('Europe/Moscow')))==='2026-10-31 21:00:00','Moscow midnight query boundary');
  $end=$pdo->query("SELECT DATE_SUB(DATE_ADD(DATE_FORMAT(DATE_ADD('2026-03-15 12:00:00',INTERVAL 3 HOUR),'%Y-%m-01'),INTERVAL 1 MONTH),INTERVAL 3 HOUR)")->fetchColumn();expect($end==='2026-03-31 21:00:00','month end converted after calendar increment, not February 28 plus month');
  $boundary=(new DateTimeImmutable($expected,new DateTimeZone('UTC')))->getTimestamp();
  $clock($boundary-$now-1);expect($service->redeem($user(),$code)['entitlement']['allowed'],'usable before deadline');
  $clock($boundary-$now);try{$service->redeem($user(),$code);throw new RuntimeException('expired accepted');}catch(DomainException $e){expect($e->getMessage()==='promo_unavailable','expired at Moscow instant');}
  $clock(0);
 });
 run('Seven remaining days plus thirty promo days give thirty-seven',function()use($pdo,$user,$create,$service):void{
  $id=$user();[$a,$ca]=$create(['duration_days'=>7]);[$b,$cb]=$create(['duration_days'=>30]);$service->redeem($id,$ca);$r=$service->redeem($id,$cb);
  $now=(string)$pdo->query('SELECT UTC_TIMESTAMP(6)')->fetchColumn();
  expect(IncidentService::micros($r['entitlement']['valid_until'])-IncidentService::micros($now)===37*86400000000,'37 days exact');
 });
 run('Concurrent promo claims respect global cap and account replay',function()use($pdo,$user,$create):void{
  $race=static function(array $ids,string $code):array{
   $workers=[];$results=[];
   foreach($ids as $id){$process=proc_open([PHP_BINARY,__DIR__.'/promo-race-worker.php',(string)$id,$code],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);expect(is_resource($process),'worker started');$workers[]=[$process,$pipes];expect(trim((string)fgets($pipes[1]))==='ready','worker connected');}
   foreach($workers as [$process,$pipes]){fwrite($pipes[0],"go\n");fclose($pipes[0]);}
   foreach($workers as [$process,$pipes]){$out=stream_get_contents($pipes[1]);$err=stream_get_contents($pipes[2]);fclose($pipes[1]);fclose($pipes[2]);expect(proc_close($process)===0&&$err==='','race succeeds');$results[]=json_decode($out,true,8,JSON_THROW_ON_ERROR);}
   return $results;
  };
  [$cid,$code]=$create();$results=$race([$user(),$user(),$user(),$user()],$code);
  expect(count(array_filter($results,static fn($r)=>$r['ok']))===1,'global cap atomic');
  [$cid2,$code2]=$create(['max_activations'=>4]);$id=$user();$results=$race([$id,$id,$id,$id],$code2);
  expect(count(array_filter($results,static fn($r)=>$r['ok']))===4,'same-account retries succeed');
  expect((int)$pdo->query('SELECT used_activations FROM promo_codes WHERE id='.$cid2)->fetchColumn()===1,'same account consumes once');
 });
 run('Promo incident freeze is compensated with immutable grant dates',function()use($pdo,$user,$create,$service,$owner,$clock):void{
  $clock(0);$id=$user();[$cid,$code]=$create();$r=$service->redeem($id,$code);$base=$r['entitlement']['valid_until'];
  $incidentService=new IncidentService($pdo);$clock(3600);$incident=$incidentService->start($owner,'Disposable promo fixture',bin2hex(random_bytes(32)));
  expect((new EntitlementService($pdo))->check($id)->reason==='service_incident','incident stops promo playback');
  $clock(7200);$incidentService->resolve($owner,$incident);
  $effective=(new EntitlementService($pdo))->check($id)->validUntil;
  expect(IncidentService::micros($effective)-IncidentService::micros($base)===3600000000,'one hour compensated');
  $q=$pdo->prepare('SELECT l.valid_until FROM entitlement_ledger l JOIN promo_redemptions r ON r.ledger_id=l.id WHERE r.id=?');$q->execute([$r['redemption_id']]);
  expect(IncidentService::micros((string)$q->fetchColumn())===IncidentService::micros($base),'base immutable');
  $pdo->exec('DELETE FROM incident_compensations WHERE incident_id='.$incident);$pdo->exec('DELETE FROM service_incidents WHERE id='.$incident);$clock(0);
 });
 run('Revoking earlier stacked promo removes only its days',function()use($pdo,$user,$create,$service,$owner):void{
  $id=$user();[$a,$ca]=$create();[$b,$cb]=$create(['duration_days'=>10]);$first=$service->redeem($id,$ca);$second=$service->redeem($id,$cb);
  $service->revokeRedemption($owner,$first['redemption_id']);$until=(new EntitlementService($pdo))->check($id)->validUntil;
  expect(IncidentService::micros($second['entitlement']['valid_until'])-IncidentService::micros($until)===30*86400000000,'second keeps own ten days');
 });
}finally{
 $pdo->exec('SET timestamp=0');
 foreach($users as $id){$pdo->exec('DELETE FROM promo_redemptions WHERE user_id='.$id);$pdo->exec('DELETE FROM account_trials WHERE user_id='.$id);$pdo->exec('DELETE FROM entitlement_ledger WHERE user_id='.$id);$pdo->exec('DELETE FROM user_email_security WHERE user_id='.$id);$pdo->exec('DELETE FROM users WHERE id='.$id);}
 foreach($codes as $id)$pdo->exec('DELETE FROM promo_codes WHERE id='.$id);
 $pdo->exec('DELETE FROM audit_log WHERE admin_id='.$owner);$pdo->exec('DELETE FROM admins WHERE id='.$owner);
}
echo "Owner promo fixtures PASS\n";
