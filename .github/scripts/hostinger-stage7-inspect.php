<?php
declare(strict_types=1);
// Read-only preflight. Deliberately no DDL, env modification, or output of credentials.
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli') exit(2);
try {
    $site = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
    $app = $site . '/celikom';
    $release = realpath($app . '/current');
    if (!$release || !str_starts_with($release, $app . '/releases/') || !is_link($app . '/current')) {
        throw new RuntimeException('release_layout');
    }
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['db_name'] !== 'u235811320_celikom') throw new RuntimeException('db_identity');
    $pdo = Celikom\Database\Connection::open($config);
    $grants = $pdo->query('SHOW GRANTS')->fetchAll(PDO::FETCH_COLUMN);
    $databaseCreate = false;
    foreach ($grants as $grant) {
        if (!is_string($grant)) continue;
        if (!preg_match('/^GRANT\s+(.+?)\s+ON\s+(.+?)\s+TO\s+/i', $grant, $m)) continue;
        $operations = strtoupper($m[1]); $scope = trim($m[2]);
        if (str_contains($operations, 'ALL PRIVILEGES') || preg_match('/(?:^|,\s*)CREATE(?:\s*,|$)/', $operations)) {
            if ($scope === '*.*' || str_contains($scope, 'u235811320\_%') ||
                str_contains($scope, 'u235811320_%')) $databaseCreate = true;
        }
    }
    $databases = $pdo->query('SHOW DATABASES')->fetchAll(PDO::FETCH_COLUMN);
    $hasStage7 = in_array('u235811320_celikom_stage7', $databases, true);
    $domains = [];
    foreach (glob('/home/u235811320/domains/*', GLOB_ONLYDIR) ?: [] as $dir) {
        if (is_dir($dir . '/public_html')) $domains[] = basename($dir);
    }
    // Public domain names only, never private filesystem content.
    echo json_encode([
        'php83' => PHP_VERSION_ID >= 80300,
        'active_catalog_intact' => (int) $pdo->query("SELECT COUNT(*) FROM track_replacements WHERE id=1 AND status='approved' AND is_active=1")->fetchColumn() === 1,
        'create_db_grant' => $databaseCreate,
        'stage7_db_exists' => $hasStage7,
        'website_domains' => $domains,
        'db_server_version' => $pdo->getAttribute(PDO::ATTR_SERVER_VERSION),
        'storage_extension' => extension_loaded('fileinfo'),
    ], JSON_THROW_ON_ERROR), "\n";
} catch (Throwable) {
    fwrite(STDERR, "Hostinger Stage 7 read-only preflight failed, no changes performed.\n");
    exit(1);
}
