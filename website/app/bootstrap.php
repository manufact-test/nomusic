<?php
declare(strict_types=1);

/**
 * CELIKOM website — private PHP bootstrap (Stage 3 scaffold).
 * On Hostinger, this directory belongs in DOMAIN_ROOT/celikom-private/app,
 * never in DOMAIN_ROOT/public_html. No settings, credentials or user data
 * should be checked into this repository.
 */
spl_autoload_register(static function (string $class): void {
    $prefix = 'Celikom\\Website\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }
    $name = substr($class, strlen($prefix));
    if ($name === '' || str_contains($name, '..')) {
        return;
    }
    $relative = str_replace('\\', '/', $name);
    $path = __DIR__ . '/src/' . $relative . '.php';
    if (is_file($path)) {
        require_once $path;
    }
});

// Optional owner-review staging credentials, read only from outside public_html.
// A public deploy cannot activate staging: a separate 0600 staging marker is mandatory.
$stagingConfigFile = dirname(__DIR__) . '/staging-config.php';
if (is_file($stagingConfigFile)) {
    $perms = fileperms($stagingConfigFile);
    if (is_link($stagingConfigFile) || !is_int($perms) || ($perms & 0077) !== 0) {
        throw new RuntimeException('Insecure private website staging configuration');
    }
    $settings = require $stagingConfigFile;
    $keys = ['CELIKOM_SITE_DB_HOST', 'CELIKOM_SITE_DB_NAME',
        'CELIKOM_SITE_DB_USER', 'CELIKOM_SITE_DB_PASSWORD',
        'CELIKOM_SITE_AUTH_HMAC_KEY', 'CELIKOM_SITE_WRITE_GATE_FILE',
        'CELIKOM_SITE_MEDIA_DIR'];
    if (!is_array($settings) || array_keys($settings) !== $keys) {
        throw new RuntimeException('Invalid private website staging configuration');
    }
    foreach ($settings as $key => $value) {
        if (!is_string($value) || $value === '' || str_contains($value, chr(0))) {
            throw new RuntimeException('Invalid private website staging setting');
        }
        if (getenv($key) === false) putenv($key . '=' . $value);
    }
}
