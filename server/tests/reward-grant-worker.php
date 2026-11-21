<?php

declare(strict_types=1);

require dirname(__DIR__).'/bootstrap.php';
$config=require dirname(__DIR__).'/config/app.php';
if (!str_starts_with((string)$config['db_name'],'celikom_test')) throw new RuntimeException('disposable_reward_grant_worker_only');
$pdo=Celikom\Database\Connection::open($config);
try {
    (new Celikom\Reward\RewardDecisionService($pdo))->decide((int)$argv[1],(int)$argv[2],1,(int)$argv[3],'approve','isolated concurrent grant');
    fwrite(STDOUT,'ok');
} catch(DomainException $error) {
    if ($error->getMessage()!=='reward_monthly_limit') throw $error;
    fwrite(STDOUT,'limit');
}
