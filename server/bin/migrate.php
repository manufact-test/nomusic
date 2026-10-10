<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
$config = require dirname(__DIR__) . '/config/app.php';
$runner = new Celikom\Database\MigrationRunner(Celikom\Database\Connection::open($config), dirname(__DIR__) . '/migrations');
foreach ($runner->run() as $migration) {
    fwrite(STDOUT, 'Applied ' . $migration . "\n");
}
fwrite(STDOUT, "Schema ready.\n");
