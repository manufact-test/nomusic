<?php
declare(strict_types=1);
namespace Celikom\Website;

use RuntimeException;

/**
 * Separate website database only. Credentials are injected from the server
 * environment; no secrets under public_html or in git.
 */
final class CmsConfig
{
    public static function databaseSettings(): array
    {
        $keys = [
            'host'=>'CELIKOM_SITE_DB_HOST',
            'dbname'=>'CELIKOM_SITE_DB_NAME',
            'user'=>'CELIKOM_SITE_DB_USER',
            'password'=>'CELIKOM_SITE_DB_PASSWORD',
        ];
        $config = [];
        foreach ($keys as $key=>$variable) {
            $value = getenv($variable);
            if (!is_string($value) || $value === '') {
                throw new RuntimeException('Dedicated website DB configuration missing');
            }
            $config[$key] = $value;
        }
        // The website must never default to the audio/catalog application DB.
        if (strtolower($config['dbname']) === 'celikom' ||
            strtolower($config['dbname']) === 'nomusic') {
            throw new RuntimeException('Use a dedicated website database');
        }
        return $config;
    }

    public static function rateSecret(): string
    {
        $secret = getenv('CELIKOM_SITE_AUTH_HMAC_KEY');
        if (!is_string($secret) || strlen($secret) < 32) {
            throw new RuntimeException('CMS login rate-limit secret missing');
        }
        return $secret;
    }
}
