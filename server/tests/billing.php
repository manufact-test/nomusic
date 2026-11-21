<?php

declare(strict_types=1);

require __DIR__ . '/smoke.php';

use Celikom\Application;
use Celikom\Billing\BillingAdapter;
use Celikom\Billing\BillingEvent;
use Celikom\Billing\BillingPlan;
use Celikom\Billing\CheckoutSession;
use Celikom\Billing\PaidAccessService;
use Celikom\Billing\SubscriptionService;
use Celikom\Billing\WebhookService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Entitlement\EntitlementService;

$config = require dirname(__DIR__) . '/config/app.php';
if (!str_starts_with($config['db_name'],'celikom_test')) throw new RuntimeException('disposable_billing_test_only');
$pdo = Connection::open($config);
(new MigrationRunner($pdo,dirname(__DIR__) . '/migrations'))->run();
$catalogBefore = $pdo->query('SELECT id,status,is_active,version FROM track_replacements ORDER BY id')->fetchAll();
$accountsBefore = $pdo->query('SELECT id,status,password_hash FROM users ORDER BY id')->fetchAll();
$secret = bin2hex(random_bytes(32));
require __DIR__ . '/billing-fixture-adapter.php';
$adapter = new BillingFixtureAdapter($secret);
$service = new SubscriptionService($pdo);
$hook = new WebhookService($pdo,$adapter);
$paid = new PaidAccessService($pdo);
$ids = [];
$metricsBefore=(new Celikom\Billing\BillingMetrics($pdo))->forPeriod(Celikom\Support\MoscowTime::today(),Celikom\Support\MoscowTime::today());
function billingExpectError(callable $call, string $expected): void {
    try { $call(); throw new RuntimeException('Expected '.$expected); }
    catch (DomainException $error) { expect($error->getMessage()===$expected,'Exact safe rejection'); }
}
$send = static function(array $data) use($hook,$secret): array {
    $body = json_encode($data,JSON_THROW_ON_ERROR);
    return $hook->handle($body,['signature'=>hash_hmac('sha256',$body,$secret)]);
};
$time = static fn(string $expression): string => (string)$pdo->query("SELECT DATE_FORMAT($expression,'%Y-%m-%d %H:%i:%s.%f')")->fetchColumn();
$now = $time('UTC_TIMESTAMP(6)');
$from = $time('DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 DAY)');
$until = $time('DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 29 DAY)');
$futureStart = $time('DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 29 DAY)');
$futureEnd = $time('DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 59 DAY)');
$older = $time('DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 HOUR)');
$newer = $time('DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 1 SECOND)');
$state = static function(string $reference) use($pdo): array {
    $q=$pdo->prepare('SELECT * FROM subscriptions WHERE provider=? AND provider_subscription_id=?');
    $q->execute(['fixture',$reference]);return $q->fetch(PDO::FETCH_ASSOC);
};
try {
    foreach ([1,2] as $index) {
        $pdo->prepare('INSERT INTO users(email,password_hash) VALUES(?,?)')
            ->execute(['billing-'.bin2hex(random_bytes(12)).'@example.invalid','fixture-not-a-login']);
        $ids[$index]=(int)$pdo->lastInsertId();
        $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES(?,UTC_TIMESTAMP(6))')->execute([$ids[$index]]);
    }
    $plan = new BillingPlan('monthly','USD',300); // Fixture price, not a production tariff.
    $sub = 'sub-'.bin2hex(random_bytes(8));
    $base = ['id'=>'evt-first','subscriptionId'=>$sub,'type'=>'paid','occurredAt'=>$now,
        'paymentId'=>'charge-first','periodStart'=>$from,'periodEnd'=>$until,'amountMinor'=>300,'currency'=>'USD'];
    run('Stage11 checkout redirect and renewal response never grant access',function()use($adapter,$plan,$service,$ids,$sub,$paid,$pdo):void{
        $url=$adapter->createCheckout($ids[1],$plan,'server-request');
        expect(str_starts_with($url->url,'https://'),'Hosted HTTPS checkout');
        $id=$service->registerPending($ids[1],'fixture',$sub,$plan);
        expect($service->registerPending($ids[1],'fixture',$sub,$plan)===$id,'Binding retry idempotent');
        billingExpectError(fn()=>$service->registerPending($ids[2],'fixture',$sub,$plan),'subscription_reference_conflict');
        $adapter->setRenewal($sub,true,'resume-request');
        expect($paid->validUntil($ids[1])===null,'No grant without confirmed charge');
        expect(!(new EntitlementService($pdo,true))->check($ids[1])->allowed,'No implicit trial or subscription access');
    });
    run('Stage11 valid charge grants exact paid window; production authority remains opt-in',function()use($send,$base,$paid,$pdo,$ids):void{
        expect($send($base)===['ok'=>true,'duplicate'=>false],'Verified event accepted');
        expect($paid->validUntil($ids[1])!==null,'Paid access available');
        expect((new EntitlementService($pdo,true))->check($ids[1])->source==='subscription','Entitlement bound to paid ledger');
        expect(!(new EntitlementService($pdo))->check($ids[1])->allowed,'Accepted Stage10 path unchanged until billing enabled');
    });
    run('Stage11 duplicate event and second notification for same charge do not duplicate money or time',function()use($send,$base,$pdo):void{
        $counts=$pdo->query('SELECT COUNT(*) FROM billing_payments')->fetchColumn();
        $ledger=$pdo->query('SELECT COUNT(*) FROM entitlement_ledger')->fetchColumn();
        expect($send($base)['duplicate'],'Exact retry');
        expect($send(array_reverse($base,true))['duplicate'],'JSON field order does not break canonical dedupe');
        $send(array_replace($base,['id'=>'evt-same-charge-other-kind']));
        expect($pdo->query('SELECT COUNT(*) FROM billing_payments')->fetchColumn()===$counts,'Charge counted once');
        expect($pdo->query('SELECT COUNT(*) FROM entitlement_ledger')->fetchColumn()===$ledger,'Time granted once');
        billingExpectError(fn()=>$send(array_replace($base,['amountMinor'=>301])),'billing_event_conflict');
        billingExpectError(fn()=>$send(array_replace($base,['id'=>'evt-wrong-currency','currency'=>'EUR'])),'billing_quote_mismatch');
    });
    run('Stage11 signature verified before duplicate lookup; malformed/unknown payments leave no residue',function()use($hook,$send,$base,$pdo):void{
        $events=$pdo->query('SELECT COUNT(*) FROM billing_events')->fetchColumn();
        billingExpectError(fn()=>$hook->handle(json_encode($base),['signature'=>'bad']),'invalid_billing_signature');
        billingExpectError(fn()=>$send(array_replace($base,['id'=>'evt-unknown','subscriptionId'=>'not-bound'])),'subscription_not_received');
        expect($pdo->query('SELECT COUNT(*) FROM billing_events')->fetchColumn()===$events,'Rejected events atomic rollback');
    });
    run('Stage11 cancel preserves paid time; delayed resume cannot undo newer cancellation',function()use($send,$sub,$newer,$older,$now,$state,$paid,$ids):void{
        $send(['id'=>'evt-cancel','subscriptionId'=>$sub,'type'=>'renewal_cancelled','occurredAt'=>$newer]);
        $send(['id'=>'evt-stale-resume','subscriptionId'=>$sub,'type'=>'renewal_resumed','occurredAt'=>$older]);
        $send(['id'=>'evt-tie-resume','subscriptionId'=>$sub,'type'=>'renewal_resumed','occurredAt'=>$newer]);
        expect((bool)$state($sub)['cancel_at_period_end'],'Cancel wins timestamp ties/stale resume');
        expect($paid->validUntil($ids[1])!==null,'Cancellation does not remove paid period');
    });
    run('Stage11 future renewal does not bridge unpaid gap; delayed failure never overrides new success',function()
        use($send,$base,$newer,$older,$futureStart,$futureEnd,$paid,$ids,$state,$sub,$until):void{
        $renewal=array_replace($base,['id'=>'evt-renew','paymentId'=>'charge-renew','periodStart'=>$futureStart,'periodEnd'=>$futureEnd,'occurredAt'=>$newer]);
        $send($renewal);
        $send(['id'=>'evt-late-fail','subscriptionId'=>$sub,'type'=>'failed','occurredAt'=>$older]);
        expect($state($sub)['status']==='active','Stale failure ignored');
        expect($paid->validUntil($ids[1])===Celikom\Entitlement\EntitlementResult::utc($until),'Future period does not grant access before start');
        expect((bool)$state($sub)['cancel_at_period_end'],'Successful payment does not re-enable renewal');
    });
    run('Stage11 partial/full refund only revokes that payment; repeats do not restore or double refund',function()use($send,$base,$now,$paid,$ids,$pdo):void{
        $refund=['id'=>'evt-partial','subscriptionId'=>$base['subscriptionId'],'type'=>'refund','occurredAt'=>$now,
            'paymentId'=>'charge-first','amountMinor'=>100,'currency'=>'USD','adjustmentId'=>'refund-part'];
        $send($refund);expect($paid->validUntil($ids[1])!==null,'Partial refund retains period');
        $send(array_replace($refund,['id'=>'evt-partial-again']));
        $sum=$pdo->query('SELECT SUM(amount_minor) FROM billing_adjustments')->fetchColumn();
        expect((int)$sum===100,'Refund counted once across notifications');
        $send(array_replace($refund,['id'=>'evt-rest','amountMinor'=>200,'adjustmentId'=>'refund-rest']));
        expect($paid->validUntil($ids[1])===null,'Full refund revokes current period; future renewal not active yet');
        $send(array_replace($base,['id'=>'evt-replayed-refunded-payment']));
        expect($paid->validUntil($ids[1])===null,'Paid replay cannot un-revoke');
        billingExpectError(fn()=>$send(array_replace($refund,['id'=>'evt-overrefund','adjustmentId'=>'refund-too-much'])),'billing_adjustment_exceeds_payment');
    });
    run('Stage11 refund arriving before charge is retryable and not consumed',function()use($send,$base,$now,$pdo):void{
        $refund=['id'=>'evt-early-refund','subscriptionId'=>$base['subscriptionId'],'type'=>'refund','occurredAt'=>$now,
            'paymentId'=>'charge-late','amountMinor'=>300,'currency'=>'USD','adjustmentId'=>'refund-early'];
        billingExpectError(fn()=>$send($refund),'payment_not_received');
        $send(array_replace($base,['id'=>'evt-late-charge','paymentId'=>'charge-late']));
        expect(!$send($refund)['duplicate'],'Retry processed after original payment');
    });
    run('Stage11 chargeback blocks affected period; disabled/unverified account remains denied',function()use($send,$base,$now,$pdo,$ids,$paid):void{
        $send(array_replace($base,['id'=>'evt-disputed-charge','paymentId'=>'charge-disputed']));
        $send(['id'=>'evt-dispute','subscriptionId'=>$base['subscriptionId'],'type'=>'chargeback','occurredAt'=>$now,
            'paymentId'=>'charge-disputed','amountMinor'=>300,'currency'=>'USD','adjustmentId'=>'dispute-one']);
        expect($paid->validUntil($ids[1])===null,'Disputed payment no longer grants');
        $send(array_replace($base,['id'=>'evt-other-paid-period','paymentId'=>'charge-valid']));
        $pdo->prepare("UPDATE users SET status='disabled' WHERE id=?")->execute([$ids[1]]);
        expect(!(new EntitlementService($pdo,true))->check($ids[1])->allowed,'Disabled account denied despite legitimate payment');
        $pdo->prepare("UPDATE users SET status='active' WHERE id=?")->execute([$ids[1]]);
        $pdo->prepare('UPDATE user_email_security SET verified_at=NULL WHERE user_id=?')->execute([$ids[1]]);
        expect(!(new EntitlementService($pdo,true))->check($ids[1])->allowed,'Unverified account denied');
        $pdo->prepare('UPDATE user_email_security SET verified_at=UTC_TIMESTAMP(6) WHERE user_id=?')->execute([$ids[1]]);
    });
    run('Stage11 concurrent deliveries grant one payment and one ledger record',function()use($pdo,$base,$secret,$ids):void{
        $event=array_replace($base,['id'=>'evt-concurrent','paymentId'=>'charge-concurrent']);
        $body=json_encode($event,JSON_THROW_ON_ERROR);
        $workers=[];
        // Separate PHP processes/connections contend on the actual account lock.
        for($i=0;$i<4;$i++) {
            $pipes=[];
            $process=proc_open([PHP_BINARY,__DIR__.'/billing-race-worker.php'],
                [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
            expect(is_resource($process),'Parallel billing worker started');
            fwrite($pipes[0],json_encode(['secret'=>$secret,'body'=>$body],JSON_THROW_ON_ERROR));
            fclose($pipes[0]);$workers[]=[$process,$pipes];
        }
        foreach($workers as [$process,$pipes]) {
            $output=stream_get_contents($pipes[1]);$error=stream_get_contents($pipes[2]);
            fclose($pipes[1]);fclose($pipes[2]);
            expect(proc_close($process)===0,'Concurrent verified delivery succeeds: '.$error);
            expect(trim($output)==='ok','Worker accepted retry');
        }
        $q=$pdo->prepare('SELECT COUNT(*) FROM billing_payments WHERE provider=? AND provider_payment_id=?');
        $q->execute(['fixture','charge-concurrent']);expect((int)$q->fetchColumn()===1,'One captured payment');
        $q=$pdo->prepare("SELECT COUNT(*) FROM entitlement_ledger l JOIN billing_payments p ON p.ledger_id=l.id
            WHERE l.user_id=? AND p.provider_payment_id='charge-concurrent'");
        $q->execute([$ids[1]]);expect((int)$q->fetchColumn()===1,'One matching grant');
    });
    run('Stage11 concurrent partial refunds cannot exceed the captured amount',function()use($pdo,$base,$send,$secret,$now):void{
        $send(array_replace($base,['id'=>'evt-refund-race-payment','paymentId'=>'charge-refund-race']));
        $workers=[];
        for($i=0;$i<2;$i++) {
            $event=['id'=>'evt-refund-race-'.$i,'subscriptionId'=>$base['subscriptionId'],'type'=>'refund',
                'occurredAt'=>$now,'paymentId'=>'charge-refund-race','amountMinor'=>200,'currency'=>'USD',
                'adjustmentId'=>'refund-race-'.$i];
            $pipes=[];$process=proc_open([PHP_BINARY,__DIR__.'/billing-race-worker.php'],
                [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
            expect(is_resource($process),'Refund worker started');
            fwrite($pipes[0],json_encode(['secret'=>$secret,'body'=>json_encode($event,JSON_THROW_ON_ERROR)],JSON_THROW_ON_ERROR));
            fclose($pipes[0]);$workers[]=[$process,$pipes];
        }
        $codes=[];
        foreach($workers as [$process,$pipes]) {
            stream_get_contents($pipes[1]);$error=stream_get_contents($pipes[2]);
            fclose($pipes[1]);fclose($pipes[2]);$codes[]=proc_close($process);
            expect($error==='','No unexpected refund error');
        }
        sort($codes);expect($codes===[0,3],'One refund accepted; excessive competing refund rejected');
        $q=$pdo->query("SELECT SUM(a.amount_minor) FROM billing_adjustments a JOIN billing_payments p ON p.id=a.payment_id
            WHERE p.provider='fixture' AND p.provider_payment_id='charge-refund-race'");
        expect((int)$q->fetchColumn()===200,'Captured amount cannot be exceeded under concurrency');
    });
    run('Stage11 expired paid period and failed renewal do not extend entitlement',function()use($pdo,$service,$send,$time,$ids,$plan,$base,$paid):void{
        $ref='expired-'.bin2hex(random_bytes(8));
        $service->registerPending($ids[2],'fixture',$ref,$plan);
        $send(array_replace($base,['id'=>'evt-expired','subscriptionId'=>$ref,'paymentId'=>'charge-expired',
            'periodStart'=>$time('DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 31 DAY)'),
            'periodEnd'=>$time('DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 DAY)')]));
        expect($paid->validUntil($ids[2])===null,'Database clock excludes ended paid period');
        $send(['id'=>'evt-expired-failure','subscriptionId'=>$ref,'type'=>'failed','occurredAt'=>$time('UTC_TIMESTAMP(6)')]);
        expect(!(new EntitlementService($pdo,true))->check($ids[2])->allowed,'Failed renewal cannot create a grant');
    });
    run('Stage11 financial totals separate currencies and count immutable money once',function()use($pdo,$send,$base,$service,$plan,$ids,$now,$metricsBefore):void{
        $ref='euro-'.bin2hex(random_bytes(8));
        $service->registerPending($ids[2],'fixture',$ref,new BillingPlan('monthly','EUR',700));
        $send(array_replace($base,['id'=>'evt-euro','subscriptionId'=>$ref,'paymentId'=>'charge-euro','amountMinor'=>700,'currency'=>'EUR']));
        $send(['id'=>'evt-euro-refund','subscriptionId'=>$ref,'type'=>'refund','occurredAt'=>$now,
            'paymentId'=>'charge-euro','amountMinor'=>100,'currency'=>'EUR','adjustmentId'=>'refund-euro']);
        $metrics=new Celikom\Billing\BillingMetrics($pdo);
        $localDay=(new DateTimeImmutable($now,new DateTimeZone('UTC')))->setTimezone(new DateTimeZone('Europe/Moscow'))->format('Y-m-d');
        $result=$metrics->forPeriod($localDay,$localDay);
        expect($result['timezone']==='Europe/Moscow','financial period uses Moscow');
        $currencies=array_column($result['currencies'],null,'currency');
        $prior=array_column($metricsBefore['currencies'],null,'currency');
        foreach(['gross_minor'=>2400,'refund_minor'=>800,'chargeback_minor'=>300,'payment_count'=>8,'first_count'=>2,'renewal_count'=>6,'after_adjustments_minor'=>1300] as $key=>$expected)
            expect($currencies['USD'][$key]-($prior['USD'][$key] ?? 0)===$expected,'USD money/count delta '.$key);
        expect($currencies['EUR']['gross_minor']-($prior['EUR']['gross_minor'] ?? 0)===700,'EUR not merged into USD');
        expect($currencies['EUR']['after_adjustments_minor']-($prior['EUR']['after_adjustments_minor'] ?? 0)===600,'Partial refund represented once');
        expect(!$result['fees_available'] && !$result['net_revenue_available'],'Unknown provider fees not presented as net revenue');
        try { $metrics->forPeriod('2026-02-30','2026-03-01');throw new RuntimeException('Invalid calendar accepted'); }
        catch(InvalidArgumentException) {}
    });
    run('Stage11 read-only subscription API is default-off, private and cannot change access',function()use($pdo,$ids,$config):void{
        $baseApp=new Application($config);
        expect($baseApp->handle('GET','/api/v1/subscription')->status===404,'Read model default off');
        $config['auth_enabled']=true;$config['billing_views_enabled']=true;
        $app=new Application($config);
        expect($app->handle('GET','/api/v1/subscription')->status===401,'Bearer required');
        $pdo->prepare('INSERT INTO user_devices(user_id,installation_id) VALUES(?,?)')->execute([$ids[1],'billing-'.bin2hex(random_bytes(12))]);
        $device=(int)$pdo->lastInsertId();$access=bin2hex(random_bytes(32));
        $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at)
            VALUES(?,?,?,?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 15 MINUTE),DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 90 DAY))')
            ->execute([$ids[1],$device,hash('sha256',$access),hash('sha256',random_bytes(32))]);
        $headers=['Authorization'=>'Bearer '.$access];
        $response=$app->handle('GET','/api/v1/subscription',query:['user_id'=>(string)$ids[2]],headers:$headers);
        expect($response->status===200 && $response->headers['Cache-Control']==='no-store','Private uncached response');
        $data=json_decode($response->body,true,32,JSON_THROW_ON_ERROR);
        expect(count($data['subscriptions'])===1 && $data['subscriptions'][0]['currency']==='USD','Query user ID cannot expose another account');
        expect(!$data['payments_available'] && !array_filter($data['actions']),'No false pay/cancel/resume buttons');
        expect(!$data['entitlement']['allowed'],'Read model never enables paid playback');
        expect($data['subscriptions'][0]['next_payment_at']===null,'No invented next charge date');
        expect(!str_contains($response->body,'charge-') && !str_contains($response->body,'evt-'),'Internal payment references remain private');
        $pdo->prepare('UPDATE user_sessions SET revoked_at=UTC_TIMESTAMP(6) WHERE user_id=?')->execute([$ids[1]]);
        expect($app->handle('GET','/api/v1/subscription',headers:$headers)->status===401,'Independent revoked session rejected');
    });
    run('Stage11 ledger corruption cannot unlock access and HTTP billing remains unregistered',function()use($pdo,$ids,$config):void{
        $pdo->prepare("UPDATE entitlement_ledger SET user_id=? WHERE id IN
            (SELECT p.ledger_id FROM billing_payments p JOIN subscriptions s ON s.id=p.subscription_id WHERE s.user_id=?)")
            ->execute([$ids[2],$ids[1]]);
        expect(!(new EntitlementService($pdo,true))->check($ids[1])->allowed,'Foreign ledger fails closed');
        $app=new Application($config);
        foreach(['/api/v1/billing/webhook','/api/v1/subscription/start','/api/v1/subscription/cancel','/api/v1/subscription/resume'] as $path) {
            expect($app->handle('POST',$path,body:'{"paid":true}')->status===404,'No test payment route on live runtime');
        }
    });
} finally {
    foreach($ids as $id) {
        $pdo->prepare('DELETE a FROM billing_adjustments a JOIN billing_payments p ON p.id=a.payment_id
            JOIN subscriptions s ON s.id=p.subscription_id WHERE s.user_id=?')->execute([$id]);
        $pdo->prepare('DELETE p FROM billing_payments p JOIN subscriptions s ON s.id=p.subscription_id WHERE s.user_id=?')->execute([$id]);
        $pdo->prepare('DELETE e FROM billing_events e JOIN subscriptions s ON s.id=e.subscription_id WHERE s.user_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM subscriptions WHERE user_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM entitlement_ledger WHERE user_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM user_email_security WHERE user_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM user_sessions WHERE user_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM user_devices WHERE user_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM users WHERE id=?')->execute([$id]);
    }
}
expect($pdo->query('SELECT id,status,is_active,version FROM track_replacements ORDER BY id')->fetchAll()===$catalogBefore,'Stage0-10 catalog preserved');
expect($pdo->query('SELECT id,status,password_hash FROM users ORDER BY id')->fetchAll()===$accountsBefore,'Existing accounts unchanged');
fwrite(STDOUT,"Stage11 isolated billing lifecycle PASS; no live provider/checkout/webhook enabled.\n");
