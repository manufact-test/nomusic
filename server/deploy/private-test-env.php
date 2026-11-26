<?php

declare(strict_types=1);

namespace Celikom\Deployment;

/** Build data for the existing, non-executable dotenv reader. */
function privateTestSettings(array $input, string $privateRoot): array
{
    foreach (['db_name', 'db_user'] as $name) {
        if (!is_string($input[$name] ?? null) || !preg_match('/^[A-Za-z0-9_]{1,64}$/D', $input[$name])) {
            throw new \InvalidArgumentException('invalid_database_identity');
        }
    }
    $password = $input['db_password'] ?? null;
    if (!is_string($password) || $password === '' || strpbrk($password, "\r\n\0") !== false) {
        throw new \InvalidArgumentException('invalid_database_password');
    }
    $host = $input['db_host'] ?? '127.0.0.1';
    if (!in_array($host, ['127.0.0.1', 'localhost'], true)) {
        throw new \InvalidArgumentException('invalid_database_host');
    }
    return [
        'APP_ENV' => 'production', 'CELIKOM_APP_DEBUG' => '0',
        'DB_HOST' => $host, 'DB_PORT' => '3306',
        'DB_NAME' => $input['db_name'], 'DB_USER' => $input['db_user'], 'DB_PASSWORD' => $password,
        'STORAGE_DRIVER' => 'local', 'STORAGE_PATH' => $privateRoot . '/shared/audio',
        'AUDIO_SIGNING_KEY' => bin2hex(random_bytes(32)),
        'API_TEST_TOKEN' => bin2hex(random_bytes(32)),
        'ANALYTICS_PRIVACY_KEY' => bin2hex(random_bytes(32)),
        'AUDIO_TOKEN_TTL_SECONDS' => '600', 'FEATURE_REPLACEMENTS' => '0', 'FEATURE_ANALYTICS' => '0',
        'ANALYTICS_RETENTION_DAYS' => '30', 'MAX_AUDIO_SIZE' => '31457280',
    ];
}

function privateTestDotenv(array $settings): string
{
    $lines = [];
    foreach ($settings as $name => $value) {
        if (!preg_match('/^[A-Z][A-Z0-9_]*$/D', $name) || !is_string($value) || strpbrk($value, "\r\n\0") !== false) {
            throw new \InvalidArgumentException('invalid_dotenv_value');
        }
        // bootstrap.php removes only the outer quotes; it never expands or executes values.
        $lines[] = $name . '="' . $value . '"';
    }
    return implode("\n", $lines) . "\n";
}
