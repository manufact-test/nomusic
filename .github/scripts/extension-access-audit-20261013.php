<?php
declare(strict_types=1);
ini_set('display_errors','0');
try {
    if (PHP_SAPI!=='cli') throw new RuntimeException('cli_only');
    $app='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release=realpath($app.'/current');
    if (!$release || !str_starts_with($release,$app.'/releases/')) throw new RuntimeException('release');
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    $pdo=Celikom\Database\Connection::open($config);
    $service=new Celikom\Entitlement\EntitlementService($pdo,(bool)($config['billing_enabled']??false));
    $counts=[];$checked=0;
    foreach ($pdo->query('SELECT id FROM users ORDER BY id LIMIT 1000')->fetchAll(PDO::FETCH_COLUMN) as $id) {
        $result=$service->check((int)$id);
        $data=$result->json();
        $key=($data['allowed']?'allowed:':'denied:').$data['source'].':'.$data['reason'];
        $counts[$key]=($counts[$key]??0)+1;$checked++;
    }
    echo json_encode(['read_only'=>true,'auth_enabled'=>(bool)$config['auth_enabled'],
        'user_uploads_enabled'=>(bool)$config['user_uploads_enabled'],'checked_accounts'=>$checked,
        'entitlement_results'=>$counts],JSON_THROW_ON_ERROR),"\n";
} catch (Throwable $e) {
    fwrite(STDERR,'Read-only access audit failed: '.($e instanceof PDOException?'database_error':'service_error')."\n");exit(1);
}
