<?php

declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
ini_set('display_errors', '0');
require __DIR__ . '/private-test-env.php';

try {
    $release = dirname(__DIR__);
    $privateRoot = dirname($release, 2);
    $site = dirname($privateRoot);
    if (basename(dirname($release)) !== 'releases' || basename($privateRoot) !== 'celikom' || !is_dir($site . '/public_html')) {
        throw new RuntimeException('invalid_private_layout');
    }
    $shared = $privateRoot . '/shared';
    if (is_link($shared) || is_link($shared . '/env') || is_link($shared . '/audio')) {
        throw new RuntimeException('invalid_private_symlink');
    }
    foreach ([$shared, $shared . '/audio', $shared . '/staging'] as $directory) {
        if (!is_dir($directory) && !mkdir($directory, 0700, true)) {
            throw new RuntimeException('private_directory_failed');
        }
        chmod($directory, 0700);
    }
    $input = json_decode(stream_get_contents(STDIN), true, 8, JSON_THROW_ON_ERROR);
    if (!is_array($input)) {
        throw new RuntimeException('invalid_input');
    }
    if (!is_file($shared . '/env')) {
        $settings = Celikom\Deployment\privateTestSettings($input, $privateRoot);
        $databaseReady = false;
        foreach (['127.0.0.1', 'localhost'] as $host) {
            try {
                $pdo = new PDO('mysql:host=' . $host . ';port=3306;dbname=' . $settings['DB_NAME'] . ';charset=utf8mb4', $settings['DB_USER'], $settings['DB_PASSWORD'], [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
                $pdo->query('SELECT 1')->fetchColumn();
                $settings['DB_HOST'] = $host;
                $databaseReady = true;
                break;
            } catch (PDOException) {
                // No credentials, exception text or connection strings in public Actions logs.
            }
        }
        if (!$databaseReady) {
            throw new RuntimeException('database_connection_failed');
        }
        $content = Celikom\Deployment\privateTestDotenv($settings);
        $handle = fopen($shared . '/env', 'x');
        if ($handle === false) {
            throw new RuntimeException('environment_creation_failed');
        }
        chmod($shared . '/env', 0600);
        if (fwrite($handle, $content) !== strlen($content)) {
            fclose($handle);
            unlink($shared . '/env');
            throw new RuntimeException('environment_write_failed');
        }
        fclose($handle);
    }
    chmod($shared . '/env', 0600);
    if (!is_link($release . '/.env')) {
        if (file_exists($release . '/.env') || !symlink($shared . '/env', $release . '/.env')) {
            throw new RuntimeException('environment_binding_failed');
        }
    }
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    Celikom\Database\Connection::open($config)->query('SELECT 1')->fetchColumn();
    // Fail BEFORE migration and public release swap if the Stage 9.1 email
    // authority is not configured. Never log SMTP identities or secrets.
    if (($config['auth_enabled'] ?? false)
        && !(new Celikom\Auth\EmailFlow(
            Celikom\Database\Connection::open($config), $config
        ))->ready()) {
        throw new RuntimeException('verified_email_sender_not_ready');
    }
    fwrite(STDOUT, "Private configuration ready; database connection verified.\n");
} catch (Throwable $error) {
    $known = ['invalid_private_layout', 'invalid_private_symlink', 'invalid_input', 'database_connection_failed', 'environment_creation_failed', 'environment_write_failed', 'environment_binding_failed'];
    $reason = in_array($error->getMessage(), $known, true) ? $error->getMessage() : 'configuration_or_database_check_failed';
    fwrite(STDERR, 'CELIKOM initialization failed: ' . $reason . "\n");
    exit(1);
}
