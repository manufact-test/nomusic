<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
try {
    $config = require dirname(__DIR__) . '/config/app.php';
    $pdo=Celikom\Database\Connection::open($config);
    $engine=str_contains((string)$pdo->query('SELECT VERSION()')->fetchColumn(),'MariaDB')?'MariaDB':'MySQL';
    fwrite(STDOUT,'Migration database engine: '.$engine."\n");
    $runner = new Celikom\Database\MigrationRunner($pdo, dirname(__DIR__) . '/migrations');
    foreach ($runner->run() as $migration) fwrite(STDOUT, 'Applied ' . $migration . "\n");
    fwrite(STDOUT, "Schema ready.\n");
} catch (\PDOException $error) {
    fwrite(STDERR,'Migration refused: SQLSTATE '.preg_replace('/[^A-Z0-9]/','',(string)($error->errorInfo[0]??''))
        .' driver '.(int)($error->errorInfo[1]??0)."\n");exit(1);
} catch (\Throwable $error) {
    $safe=in_array($error->getMessage(),['migration_lock_unavailable','migration_unreadable','applied_migration_changed'],true)
        ?$error->getMessage():'migration_failed';
    fwrite(STDERR,'Migration refused: '.$safe."\n");exit(1);
}
