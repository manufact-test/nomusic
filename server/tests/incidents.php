<?php

declare(strict_types=1);

require __DIR__.'/smoke.php';

use Celikom\Incident\IncidentService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Entitlement\TrialService;
use Celikom\Entitlement\EntitlementService;
use Celikom\Admin\AdminAuth;
use Celikom\Application;

$config = require dirname(__DIR__).'/config/app.php';
if (!str_starts_with($config['db_name'],'celikom_test')) throw new RuntimeException('disposable_incident_tests_only');
$pdo=Connection::open($config);(new MigrationRunner($pdo,dirname(__DIR__).'/migrations'))->run();
$service=new IncidentService($pdo);
$accounts=$pdo->query('SELECT id,status,password_hash FROM users ORDER BY id')->fetchAll();
$catalog=$pdo->query('SELECT id,status,is_active FROM track_replacements ORDER BY id')->fetchAll();
run('Stage13 microsecond precision, 3d6h freeze and overlap union use UTC',function():void {
 $from='2026-10-01 00:00:00.123456';$until='2026-10-04 00:00:00.123456';
 $outage=[['2026-10-02 00:00:00.123456','2026-10-05 06:00:00.123456']];
 expect(IncidentService::extendedUntil($from,$until,$outage)==='2026-10-07 06:00:00.123456','3d6h exactly, even past original expiry');
 $outage[]=['2026-10-03 00:00:00.123456','2026-10-04 01:00:00.123456'];
 expect(IncidentService::extendedUntil($from,$until,$outage)==='2026-10-07 06:00:00.123456','nested overlap once');
 expect(IncidentService::extendedUntil('2026-10-03 00:00:00.123456','2026-10-06 00:00:00.123456',$outage)==='2026-10-08 06:00:00.123456','trial started during incident');
 expect(IncidentService::extendedUntil('2026-09-01 00:00:00.000000','2026-09-04 00:00:00.000000',$outage)==='2026-09-04 00:00:00.000000','expired before outage unaffected');
 expect(IncidentService::micros('2026-10-25T02:30:00+02:00')+3600000000===IncidentService::micros('2026-10-25T02:30:00+01:00'),'DST instant arithmetic');
});
$login='incident-'.bin2hex(random_bytes(6));$password='fixture-'.bin2hex(random_bytes(8));
$pdo->prepare("INSERT INTO admins(login,password_hash,role) VALUES (?,?,'owner')")->execute([$login,password_hash($password,PASSWORD_DEFAULT)]);
$admin=(int)$pdo->lastInsertId();$ids=[];
$now=(int)$pdo->query('SELECT UNIX_TIMESTAMP(UTC_TIMESTAMP())')->fetchColumn();
$clock=static function(int $seconds)use($pdo,$now):void{$pdo->exec('SET timestamp='.($now+$seconds));};
$addUser=static function()use($pdo,&$ids):int {
 $pdo->prepare('INSERT INTO users(email,password_hash) VALUES (?,?)')->execute(['incident-'.bin2hex(random_bytes(8)).'@example.invalid','fixture-not-login']);
 $id=(int)$pdo->lastInsertId();$ids[]=$id;$pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES (?,UTC_TIMESTAMP(6))')->execute([$id]);return $id;
};
try {
 $clock(0);$id=$addUser();(new TrialService($pdo))->activate($id);
 $paidUser=$addUser();$secret=bin2hex(random_bytes(32));
 require __DIR__.'/billing-fixture-adapter.php';
 $subscription='incident-sub-'.bin2hex(random_bytes(8));
 (new Celikom\Billing\SubscriptionService($pdo))->registerPending($paidUser,'fixture',$subscription,new Celikom\Billing\BillingPlan('monthly','USD',300));
 $paidFrom=$pdo->query("SELECT DATE_FORMAT(UTC_TIMESTAMP(6),'%Y-%m-%d %H:%i:%s.%f')")->fetchColumn();
 $paidUntil=$pdo->query("SELECT DATE_FORMAT(DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 30 DAY),'%Y-%m-%d %H:%i:%s.%f')")->fetchColumn();
 $body=json_encode(['id'=>'incident-paid','subscriptionId'=>$subscription,'type'=>'paid','occurredAt'=>$paidFrom,'paymentId'=>'incident-charge','periodStart'=>$paidFrom,'periodEnd'=>$paidUntil,'amountMinor'=>300,'currency'=>'USD'],JSON_THROW_ON_ERROR);
 (new Celikom\Billing\WebhookService($pdo,new BillingFixtureAdapter($secret)))->handle($body,['signature'=>hash_hmac('sha256',$body,$secret)]);
 $original=$pdo->query('SELECT valid_from,valid_until,ledger_id FROM account_trials WHERE user_id='.$id)->fetch(PDO::FETCH_ASSOC);
 $clock(3600);$key=bin2hex(random_bytes(32));$incident=$service->start($admin,'Confirmed test outage',$key);
 run('Stage13 start retry, incident config and access freeze do not reset trial',function()use($service,$admin,$key,$incident,$pdo,$id,$config,$original):void {
  expect($service->start($admin,'Confirmed test outage',$key)===$incident,'start key idempotent');
  $state=(new EntitlementService($pdo))->check($id);expect(!$state->allowed && $state->reason==='service_incident','replacement suspended');
  $config['entitlement_enabled']=true;$response=(new Application($config))->handle('GET','/api/v1/config');
  expect($response->status===200 && json_decode($response->body,true)['incident']['active'],'public incident state');
  expect(!(new TrialService($pdo))->activate($id)['activated'],'activation retry no reset');
  expect($pdo->query('SELECT valid_until FROM account_trials WHERE user_id='.$id)->fetchColumn()===$original['valid_until'],'immutable base trial');
 });
 $clock(7200);$second=$service->start($admin,'Second overlapping outage',bin2hex(random_bytes(32)));
 $partial=$addUser();(new TrialService($pdo))->activate($partial);
 $clock(10800);$other=$service->start($admin,'Other adapter outage',bin2hex(random_bytes(32)),'future_adapter');
 $clock(14400);$service->resolve($admin,$incident);
 $clock(18000);$service->resolve($admin,$second);
 run('Stage13 overlapping resolves allocate only new downtime and retry never adds compensation',function()use($service,$admin,$incident,$second,$pdo,$id,$original,$partial,$other):void {
  $q=$pdo->prepare('SELECT SUM(microseconds) FROM incident_compensations WHERE ledger_id=?');$q->execute([$original['ledger_id']]);
  expect((int)$q->fetchColumn()===14400000000,'four hours union, not seven');
  $before=$pdo->query('SELECT * FROM incident_compensations ORDER BY id')->fetchAll();
  expect(!$service->resolve($admin,$second) && !$service->resolve($admin,$incident),'duplicate completion');
  expect($pdo->query('SELECT * FROM incident_compensations ORDER BY id')->fetchAll()===$before,'no second grant');
  $state=(new EntitlementService($pdo))->check($id);expect($state->allowed,'other adapter does not freeze Yandex');
  expect(IncidentService::micros(str_replace(['T','Z'],[' ',''],$state->validUntil))-IncidentService::micros($original['valid_until'])===14400000000,'effective trial includes compensation');
  $row=$pdo->query('SELECT t.valid_until,SUM(c.microseconds) AS credited FROM account_trials t JOIN incident_compensations c ON c.ledger_id=t.ledger_id WHERE t.user_id='.$partial.' GROUP BY t.valid_until')->fetch();
  expect((int)$row['credited']===10800000000,'late starter receives three hours');
 });
 run('Stage13 paid grants extend exactly while billing stays opt-in; revoked payments stay revoked',function()use($pdo,$paidUser,$paidUntil):void{
  $paid=new Celikom\Billing\PaidAccessService($pdo);
  expect(IncidentService::micros($paid->validUntil($paidUser))-IncidentService::micros($paidUntil)===14400000000,'paid period receives union exactly');
  expect(!(new EntitlementService($pdo))->check($paidUser)->allowed,'production billing still disabled');
  expect((new EntitlementService($pdo,true))->check($paidUser)->allowed,'fixture opt-in paid entitlement');
  $pdo->exec('UPDATE billing_payments p JOIN subscriptions s ON s.id=p.subscription_id SET p.revoked_at=UTC_TIMESTAMP(6) WHERE s.user_id='.$paidUser);
  expect($paid->validUntil($paidUser)===null,'compensation never revives revoked payment');
 });
 run('Stage13 failed audit rolls back completion and compensation atomically',function()use($pdo,$admin,$other,$service):void{
  $pdo->exec("CREATE TRIGGER stage13_audit_failure BEFORE INSERT ON audit_log FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='fixture_failure'");
  try { try {$service->resolve($admin,$other);throw new RuntimeException('audit failure ignored');} catch(PDOException){} }
  finally {$pdo->exec('DROP TRIGGER stage13_audit_failure');}
  expect($pdo->query('SELECT ended_at FROM service_incidents WHERE id='.$other)->fetchColumn()===null,'resolution rolled back');
  expect((int)$pdo->query('SELECT COUNT(*) FROM incident_compensations WHERE incident_id='.$other)->fetchColumn()===0,'credits rolled back');
  expect($service->resolve($admin,$other),'retry after rollback');
 });
 run('Stage13 concurrent resolution allocates downtime once across separate connections',function()use($pdo,$service,$clock,$admin,$original):void{
  $clock(21600);$race=$service->start($admin,'Concurrent fixture',bin2hex(random_bytes(32)));
  $workers=[];
  for($i=0;$i<4;$i++){
   $pipes=[];$process=proc_open([PHP_BINARY,__DIR__.'/incident-race-worker.php'],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
   expect(is_resource($process),'worker started');fwrite($pipes[0],json_encode(['admin'=>$admin,'incident'=>$race,'timestamp'=>(int)$pdo->query('SELECT UNIX_TIMESTAMP(UTC_TIMESTAMP())')->fetchColumn()+3600],JSON_THROW_ON_ERROR));fclose($pipes[0]);$workers[]=[$process,$pipes];
  }
  $changed=0;
  foreach($workers as [$process,$pipes]){
   $output=stream_get_contents($pipes[1]);$error=stream_get_contents($pipes[2]);fclose($pipes[1]);fclose($pipes[2]);
   expect(proc_close($process)===0,'resolution race succeeds: '.$error);$changed+=(int)trim($output);
  }
  expect($changed===1,'one resolution');
  $q=$pdo->prepare('SELECT COUNT(*),SUM(microseconds) FROM incident_compensations WHERE incident_id=? AND ledger_id=?');$q->execute([$race,$original['ledger_id']]);$row=$q->fetch(PDO::FETCH_NUM);
  expect((int)$row[0]===1 && (int)$row[1]===3600000000,'one hour credited once');
 });
 run('Stage13 admin endpoints enforce owner and CSRF; stored reasons are escaped',function()use($pdo,$config,$login,$password,$admin):void {
  $config['admin_enabled']=true;$app=new Application($config);$identity=(new AdminAuth($pdo))->login($login,$password,'fixture-incidents');
  $headers=['Cookie'=>AdminAuth::COOKIE.'='.$identity['token'],'Content-Type'=>'application/x-www-form-urlencoded'];
  $body=http_build_query(['reason'=>'<script>bad</script>','request_key'=>bin2hex(random_bytes(32)),'csrf'=>AdminAuth::csrfForToken($identity['token'])]);
  expect($app->handle('POST','/admin/incidents/start',headers:$headers,body:'reason=x')->status===403,'CSRF enforced');
  $pdo->exec("UPDATE admins SET role='moderator' WHERE id=$admin");
  expect($app->handle('POST','/admin/incidents/start',headers:$headers,body:$body)->status===403,'owner only');
  expect($app->handle('GET','/admin',query:['tab'=>'incidents'],headers:$headers)->status===403,'view owner only');
  $pdo->exec("UPDATE admins SET role='owner' WHERE id=$admin");
  expect($app->handle('POST','/admin/incidents/start',headers:$headers,body:$body)->status===303,'owner action');
  $view=$app->handle('GET','/admin',query:['tab'=>'incidents'],headers:$headers);expect(str_contains($view->body,'&lt;script&gt;bad&lt;/script&gt;'),'HTML escaped');
 });
} finally {
 $pdo->exec('SET timestamp=0');
 $pdo->exec('DELETE c FROM incident_compensations c JOIN service_incidents i ON i.id=c.incident_id WHERE i.created_by='.$admin);
 $pdo->exec('DELETE FROM service_incidents WHERE created_by='.$admin);
 $pdo->exec('DELETE FROM audit_log WHERE admin_id='.$admin);
 $pdo->exec('DELETE FROM admin_sessions WHERE admin_id='.$admin);
 $pdo->exec('DELETE FROM admins WHERE id='.$admin);
 foreach($ids as $id){
 $pdo->exec('DELETE p FROM billing_payments p JOIN subscriptions s ON s.id=p.subscription_id WHERE s.user_id='.$id);
 $pdo->exec('DELETE e FROM billing_events e JOIN subscriptions s ON s.id=e.subscription_id WHERE s.user_id='.$id);
 $pdo->exec('DELETE FROM subscriptions WHERE user_id='.$id);
 $pdo->exec('DELETE FROM account_trials WHERE user_id='.$id);$pdo->exec('DELETE FROM entitlement_ledger WHERE user_id='.$id);$pdo->exec('DELETE FROM user_email_security WHERE user_id='.$id);$pdo->exec('DELETE FROM users WHERE id='.$id);}
}
expect($pdo->query('SELECT id,status,password_hash FROM users ORDER BY id')->fetchAll()===$accounts,'real accounts preserved');
expect($pdo->query('SELECT id,status,is_active FROM track_replacements ORDER BY id')->fetchAll()===$catalog,'catalog preserved');
