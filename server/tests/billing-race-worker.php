<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
require __DIR__ . '/billing-fixture-adapter.php';

$config = require dirname(__DIR__) . '/config/app.php';
if (PHP_SAPI !== 'cli' || !str_starts_with((string)$config['db_name'],'celikom_test')) exit(10);
try {
    $input=json_decode(stream_get_contents(STDIN),true,32,JSON_THROW_ON_ERROR);
    $adapter=new BillingFixtureAdapter($input['secret']);
    $pdo=Celikom\Database\Connection::open($config);
    (new Celikom\Billing\WebhookService($pdo,$adapter))->handle($input['body'],
        ['signature'=>hash_hmac('sha256',$input['body'],$input['secret'])]);
    fwrite(STDOUT,"ok\n");
    exit(0);
} catch (DomainException $error) {
    if ($error->getMessage()==='billing_adjustment_exceeds_payment') exit(3);
    fwrite(STDERR,$error->getMessage());
    exit(9);
} catch (Throwable $error) {
    fwrite(STDERR,get_class($error).': '.$error->getMessage());
    exit(9);
}
