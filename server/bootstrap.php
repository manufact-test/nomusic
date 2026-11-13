<?php

declare(strict_types=1);

spl_autoload_register(static function (string $class): void {
    $prefix = 'Celikom\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }
    $file = __DIR__ . '/src/' . str_replace('\\', '/', substr($class, strlen($prefix))) . '.php';
    if (is_file($file)) {
        require $file;
    }
});

// Only data, never executable PHP or shell interpolation. Environment wins.
$envFile = __DIR__ . '/.env';
if (is_file($envFile)) {
    foreach (file($envFile, FILE_IGNORE_NEW_LINES) ?: [] as $line) {
        if (!preg_match('/^\s*([A-Z][A-Z0-9_]*)\s*=(.*)$/', $line, $match)) {
            continue;
        }
        if (getenv($match[1]) !== false) {
            continue;
        }
        $value = trim($match[2]);
        if (strlen($value) >= 2 && (($value[0] === '"' && str_ends_with($value, '"')) || ($value[0] === "'" && str_ends_with($value, "'")))) {
            $value = substr($value, 1, -1);
        }
        putenv($match[1] . '=' . $value);
    }
}
