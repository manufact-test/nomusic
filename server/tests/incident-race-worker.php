<?php
declare(strict_types=1);
require dirname(__DIR__).'/bootstrap.php';
$config=require dirname(__DIR__).'/config/app.php';
if(PHP_SAPI!=='cli' || !str_starts_with($config['db_name'],'celikom_test')) exit(10);
try {
    $input=json_decode(stream_get_contents(STDIN),true,8,JSON_THROW_ON_ERROR);
    $pdo=Celikom\Database\Connection::open($config);
    $pdo->exec('SET timestamp='.(int)$input['timestamp']);
    $changed=(new Celikom\Incident\IncidentService($pdo))->resolve((int)$input['admin'],(int)$input['incident']);
    fwrite(STDOUT,$changed?"1\n":"0\n");
} catch(Throwable $error) { fwrite(STDERR,get_class($error).': '.$error->getMessage());exit(9); }
