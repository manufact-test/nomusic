<?php

declare(strict_types=1);

require dirname(__DIR__).'/bootstrap.php';
$config=require dirname(__DIR__).'/config/app.php';
if (!str_starts_with((string)$config['db_name'],'celikom_test')) throw new RuntimeException('disposable_reward_worker_only');
$pdo=Celikom\Database\Connection::open($config);
$pdo->beginTransaction();
try {
    (new Celikom\Reward\RewardService($pdo))->recordApprovedUpload((int)$argv[1],(int)$argv[2]);
    $pdo->commit();fwrite(STDOUT,'ok');
} catch(Throwable $error) {
    if($pdo->inTransaction()) $pdo->rollBack();throw $error;
}
