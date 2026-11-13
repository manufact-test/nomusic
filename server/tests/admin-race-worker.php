<?php

declare(strict_types=1);

// Dedicated parallel CI worker: no production credentials, only disposable MySQL.
require dirname(__DIR__) . '/bootstrap.php';

$config=require dirname(__DIR__) . '/config/app.php';
if (PHP_SAPI !== 'cli' || !str_starts_with((string)$config['db_name'],'celikom_test')
    || !isset($argv[1],$argv[2])
    || !ctype_digit($argv[1]) || !ctype_digit($argv[2])) exit(10);

try {
    $pdo=Celikom\Database\Connection::open($config);
    $storage=new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    (new Celikom\Admin\ModerationService($pdo,$storage))
        ->replacement((int)$argv[1],(int)$argv[2],'approve','stage8 approved race fixture',0,true);
    exit(0);
} catch (DomainException $e) {
    // Expected loser: active mapping changed while waiting for the Track row lock.
    if (in_array($e->getMessage(),['stale_moderation_form','candidate_not_pending'],true)) exit(3);
    exit(9);
} catch (Throwable) {
    exit(9);
}
