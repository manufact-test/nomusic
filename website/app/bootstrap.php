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
