<?php
declare(strict_types=1);
require dirname(__DIR__).'/bootstrap.php';
$config=require dirname(__DIR__).'/config/app.php';
if (PHP_SAPI!=='cli' || !str_starts_with((string)$config['db_name'],'celikom_test')
    || !isset($argv[1]) || !ctype_digit($argv[1])) exit(10);
try {
    $pdo=Celikom\Database\Connection::open($config);
    fwrite(STDOUT,(new Celikom\Referral\ReferralService($pdo))->code((int)$argv[1]));
} catch (Throwable $error) { fwrite(STDERR,get_class($error).': '.$error->getMessage());exit(9); }
