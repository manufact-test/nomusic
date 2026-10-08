<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
$config = require dirname(__DIR__) . '/config/app.php';
if (!$config['analytics_enabled']) {
    fwrite(STDOUT, "Analytics disabled.\n");
    exit(0);
}
$service = new Celikom\Analytics\AnalyticsQueryService(Celikom\Database\Connection::open($config));
foreach ([gmdate('Y-m-d', time() - 86400), gmdate('Y-m-d')] as $day) {
    $service->aggregateDay($day);
}
$service->purge($config['analytics_retention_days']);
fwrite(STDOUT, "UTC product counters updated.\n");
