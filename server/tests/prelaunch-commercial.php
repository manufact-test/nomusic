<?php

declare(strict_types=1);

// Disposable CI-only end-to-end money authority contract. No production DB,
// no real payment, no public audio and no live account can be used by mistake.
require __DIR__ . '/smoke.php';

use Celikom\Application;
use Celikom\Application\AudioTokenService;
use Celikom\Billing\BillingPlan;
use Celikom\Billing\SubscriptionService;
use Celikom\Billing\WebhookService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Repositories\CatalogRepository;
use Celikom\Storage\LocalStorageAdapter;

$config = require dirname(__DIR__) . '/config/app.php';
if ($config['environment'] !== 'test' || !str_starts_with($config['db_name'], 'celikom_test')
    || getenv('CI') !== 'true') {
    throw new RuntimeException('W68_DISPOSABLE_TEST_DATABASE_REQUIRED');
}

$pdo = Connection::open($config);
(new MigrationRunner($pdo, dirname(__DIR__) . '/migrations'))->run();
$directory = sys_get_temp_dir() . '/celikom-commercial-' . bin2hex(random_bytes(10));
$storage = new LocalStorageAdapter($directory);
$stream = fopen('php://temp', 'w+b');
fwrite($stream, '0123456789abcdef');
rewind($stream);
$storage->put('audio/w68-fixture.mp3', $stream);
fclose($stream);
$row = ['replacement_id'=>777, 'version'=>1, 'storage_driver'=>'local',
    'storage_key'=>'audio/w68-fixture.mp3', 'sha256'=>str_repeat('b', 64),
    'mime_type'=>'audio/mpeg', 'size_bytes'=>16, 'duration_ms'=>210000];
$catalog = new class($row) implements CatalogRepository {
    public function __construct(private readonly array $row) {}
    public function findActive(string $service, string $trackId): ?array
    {
        return $service==='yandex' && $trackId==='1944599' ? $this->row : null;
    }
    public function findByReplacement(int $id): ?array
    {
        return $id===777 ? $this->row : null;
    }
};

function fixtureCommercialAccount(PDO $pdo, string $tag): array
{
    $email = 'w68-' . $tag . '-' . bin2hex(random_bytes(8)) . '@example.invalid';
    $pdo->prepare('INSERT INTO users(email,password_hash) VALUES(?,?)')->execute([$email,'offline-fixture']);
    $user = (int)$pdo->lastInsertId();
    $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES(?,UTC_TIMESTAMP(6))')->execute([$user]);
    $install = sprintf('8de936d6-2af5-4ca7-973f-%012d', $user % 1000000000000);
    $pdo->prepare('INSERT INTO user_devices(user_id,installation_id) VALUES(?,?)')->execute([$user,$install]);
    $device=(int)$pdo->lastInsertId();
    $bearer=bin2hex(random_bytes(32));
    $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at)
        VALUES(?,?,?,?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 15 MINUTE),DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 90 DAY))')
        ->execute([$user,$device,hash('sha256',$bearer),hash('sha256',random_bytes(32))]);
    return [$user,$bearer,(int)$pdo->lastInsertId()];
}

[$customer,$token,$session] = fixtureCommercialAccount($pdo,'paid');
[$unpaid,$unpaidToken] = fixtureCommercialAccount($pdo,'unpaid');
$cfg = $config;
$cfg['api_enabled'] = true;
$cfg['auth_enabled'] = true;
$cfg['entitlement_enabled'] = true;
$cfg['audio_signing_key'] = str_repeat('w68-server-test-key-', 3);
$cfg['test_api_token'] = str_repeat('legacy-beta-bearer-', 4);
$cfg['paid_entitlement_enabled'] = false;
$api = fn(array $cfg): Application => new Application($cfg, $catalog, $storage);
$head = ['Authorization'=>'Bearer ' . $token,'Content-Type'=>'application/json'];
$other = ['Authorization'=>'Bearer ' . $unpaidToken];
$query=['service'=>'yandex','track_id'=>'1944599'];
$parse = static fn($res): array => json_decode($res->body, true, flags: JSON_THROW_ON_ERROR);

run('W68 zero-payment and legacy beta tokens never authorize commercial playback', function() use($api,$cfg,$head,$other,$query,$parse):void {
    $app=$api($cfg);
    expect($parse($app->handle('GET','/api/v1/entitlement',headers:$head))['allowed']===false,'No entitlement just because logged in');
    expect($app->handle('GET','/api/v1/resolve',$query,$head)->status===403,'Unpaid resolve denied');
    expect($app->handle('GET','/api/v1/resolve',$query,$other)->status===403,'Other unpaid account denied');
    $legacy=['Authorization'=>'Bearer '.$cfg['test_api_token']];
    expect($app->handle('GET','/api/v1/resolve',$query,$legacy)->status!==200,'Legacy token cannot bypass trial');
});

$secret=bin2hex(random_bytes(32));
require __DIR__ . '/billing-fixture-adapter.php';
$adapter=new BillingFixtureAdapter($secret);
$subs=new SubscriptionService($pdo);
$hook=new WebhookService($pdo,$adapter);
$subscription='w68-sub-'.bin2hex(random_bytes(8));
$subs->registerPending($customer,'fixture',$subscription,new BillingPlan('monthly','USD',300));
$time=static fn(string $sql):string=>(string)$pdo->query("SELECT DATE_FORMAT($sql,'%Y-%m-%d %H:%i:%s.%f')")->fetchColumn();
$from=$time('DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 1 DAY)');
$until=$time('DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 29 DAY)');
$paid=['id'=>'w68-paid-event','subscriptionId'=>$subscription,'type'=>'paid','occurredAt'=>$time('UTC_TIMESTAMP(6)'),
    'paymentId'=>'w68-charge','periodStart'=>$from,'periodEnd'=>$until,'amountMinor'=>300,'currency'=>'USD'];
$send=static function(array $event)use($hook,$secret):array {
    $body=json_encode($event,JSON_THROW_ON_ERROR);
    return $hook->handle($body,['signature'=>hash_hmac('sha256',$body,$secret)]);
};

run('W68 unverified pending checkout does not unlock playback',function()use($api,$cfg,$head,$query):void{
    $on=$cfg;$on['paid_entitlement_enabled']=true;$app=$api($on);
    expect($app->handle('GET','/api/v1/resolve',$query,$head)->status===403,'Pending purchase denied');
});

expect($send($paid)['ok']===true,'Signed fixture provider accepted a genuine payment');
run('W68 confirmed paid ledger works ONLY with explicit commercial flag and server session',function()use($api,$cfg,$head,$other,$query,$parse,$paid,$customer):void{
    $off=$api($cfg);
    expect($off->handle('GET','/api/v1/resolve',$query,$head)->status===403,'Default OFF refuses paid-only access');
    $on=$cfg;$on['paid_entitlement_enabled']=true;$app=$api($on);
    $entitlement=$parse($app->handle('GET','/api/v1/entitlement',headers:$head));
    expect($entitlement['allowed']===true && $entitlement['source']==='subscription'
        && str_ends_with($entitlement['valid_until'],'Z'),'Verified paid account recognized by own email bearer');
    $r=$app->handle('GET','/api/v1/resolve',$query,$head);
    $grant=$parse($r);expect($r->status===200 && $grant['found']===true,'Confirmed payer can resolve');
    parse_str(parse_url($grant['audio_url'],PHP_URL_QUERY),$signed);
    $audioPath=(string)parse_url($grant['audio_url'],PHP_URL_PATH);
    expect(isset($signed['sid']) && $app->handle('GET',$audioPath,$signed,['Range'=>'bytes=0-3'])->status===206,
        'Real Range rechecks paid session and returns 206');
    expect($app->handle('GET','/api/v1/resolve',$query,$other)->status===403,'Another user cannot inherit payment');
    $anonymous=new AudioTokenService($on['audio_signing_key']);
    $legacy=['expires'=>(string)$grant['expires_at'],
        'token'=>$anonymous->sign((int)$grant['replacement_id'],(int)$grant['version'],(int)$grant['expires_at'])];
    expect($app->handle('GET',$audioPath,$legacy)->status===403,'Correctly signed legacy v1 URL cannot bypass user session');
    expect($off->handle('GET',$audioPath,$signed)->status===403,'Turning off paid feature revokes previously issued grant');
});

$refund=['id'=>'w68-refund-event','subscriptionId'=>$subscription,'type'=>'refund','occurredAt'=>$time('UTC_TIMESTAMP(6)'),
    'paymentId'=>'w68-charge','adjustmentId'=>'w68-full-refund','amountMinor'=>300,'currency'=>'USD'];
expect($send($refund)['ok']===true,'Genuine signed refund accepted');
run('W68 refund, failure and no trial cannot become unlimited access',function()use($api,$cfg,$head,$query,$parse):void{
    $on=$cfg;$on['paid_entitlement_enabled']=true;$app=$api($on);
    expect($app->handle('GET','/api/v1/resolve',$query,$head)->status===403,'Fully refunded paid period denied');
    $ent=$parse($app->handle('GET','/api/v1/entitlement',headers:$head));
    expect($ent['allowed']===false && $ent['reason']==='trial_not_started','No unlimited fallback after chargeback/refund');
});
echo "W68_PAYMENT_TRIAL_AUTH_SESSION_RANGE_AND_REFUND_PASS\n";
