<?php

declare(strict_types=1);
require dirname(__DIR__).'/bootstrap.php';
$config=require dirname(__DIR__).'/config/app.php';
if(PHP_SAPI!=='cli'||!str_starts_with($config['db_name'],'celikom_test')||!ctype_digit($argv[1]??'')||!preg_match('/^[A-Z0-9_-]{8,64}$/D',$argv[2]??''))exit(10);
try{
 $pdo=Celikom\Database\Connection::open($config);fwrite(STDOUT,"ready\n");fflush(STDOUT);
 if(trim((string)fgets(STDIN))!=='go')exit(10);
 try{$r=(new Celikom\Promo\PromoService($pdo))->redeem((int)$argv[1],$argv[2]);$out=['ok'=>true,'replay'=>$r['already_activated']];}
 catch(DomainException $e){$out=['ok'=>false,'error'=>$e->getMessage()];}
 fwrite(STDOUT,json_encode($out,JSON_THROW_ON_ERROR));
}catch(Throwable $e){fwrite(STDERR,get_class($e));exit(9);}
