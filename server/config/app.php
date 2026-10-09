<?php

declare(strict_types=1);

$value = static fn (string $name, string $default = ''): string => getenv($name) !== false ? (string) getenv($name) : $default;
$boolean = static fn (string $name): bool => filter_var(getenv($name) ?: '0', FILTER_VALIDATE_BOOL);

return [
    'environment' => $value('APP_ENV', $value('CELIKOM_APP_ENV', 'local')),
    'debug' => $boolean('CELIKOM_APP_DEBUG'),
    'version' => '0.4.0',
    'db_host' => $value('DB_HOST', '127.0.0.1'),
    'db_port' => (int) $value('DB_PORT', '3306'),
    'db_name' => $value('DB_NAME'),
    'db_user' => $value('DB_USER'),
    'db_password' => $value('DB_PASSWORD'),
    'storage_driver' => $value('STORAGE_DRIVER', 'local'),
    'storage_path' => $value('STORAGE_PATH', dirname(__DIR__) . '/storage/audio'),
    'audio_signing_key' => $value('AUDIO_SIGNING_KEY'),
    'audio_token_ttl' => (int) $value('AUDIO_TOKEN_TTL_SECONDS', '600'),
    'resolve_cache_ttl_seconds' => (int) $value('RESOLVE_CACHE_TTL_SECONDS', '120'),
    'negative_cache_ttl_seconds' => (int) $value('NEGATIVE_CACHE_TTL_SECONDS', '15'),
    'test_api_token' => $value('API_TEST_TOKEN'),
    'owner_upload_token' => $value('UPLOAD_OWNER_TOKEN'),
    'owner_uploads_enabled' => $boolean('FEATURE_OWNER_UPLOADS'),
    'admin_enabled' => $boolean('FEATURE_ADMIN'),
    'owner_reports_enabled' => $boolean('FEATURE_OWNER_REPORTS'),
    'owner_report_token' => $value('REPORT_OWNER_TOKEN'),
    'api_enabled' => $boolean('FEATURE_REPLACEMENTS'),
    'analytics_enabled' => $boolean('FEATURE_ANALYTICS'),
    'analytics_privacy_key' => $value('ANALYTICS_PRIVACY_KEY'),
    'analytics_retention_days' => (int) $value('ANALYTICS_RETENTION_DAYS', '30'),
    'max_audio_size' => (int) $value('MAX_AUDIO_SIZE', '31457280'),
    'minimum_extension_version' => '0.4.0',
    'allowed_origins' => $value('APP_ENV') === 'test' && str_starts_with($value('CELIKOM_TEST_ORIGIN'), 'http://127.0.0.1:')
        ? ['https://music.yandex.ru', $value('CELIKOM_TEST_ORIGIN')]
        : ['https://music.yandex.ru'],
];
