<?php
declare(strict_types=1);
namespace Celikom\Website;

/**
 * Owner-review gate for Hostinger environments where .htaccess Basic Auth is
 * ignored upstream. Enforced separately on BOTH PHP entrypoints. Assets may
 * remain fetchable; never store confidential data in public/ assets.
 */
final class CmsStagingHttpAuth
{
    public static function enforce(string $privateAppDirectory): void
    {
        $app = realpath($privateAppDirectory);
        if (!is_string($app) || !is_dir($app)) {
            self::deny(503);
        }
        $passwd = dirname($app).'/.htpasswd';
        if (!is_file($passwd) || is_link($passwd) ||
            (fileperms($passwd) & 0077) !== 0) {
            self::deny(503);
        }
        $entry = trim((string)file_get_contents($passwd));
        if (!preg_match('/^review:(\$2[aby]\$[0-9]{2}\$[.\/A-Za-z0-9]{53})$/D', $entry, $found)) {
            self::deny(503);
        }
        $username = $_SERVER['PHP_AUTH_USER'] ?? null;
        $password = $_SERVER['PHP_AUTH_PW'] ?? null;
        if (!is_string($username) || !is_string($password)) {
            $authorization = $_SERVER['HTTP_AUTHORIZATION']
                ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
            if (is_string($authorization) && strlen($authorization) <= 512
                && preg_match('/^Basic ([A-Za-z0-9+\/=]+)$/D', $authorization, $m)) {
                $decoded = base64_decode($m[1], true);
                if (is_string($decoded) && str_contains($decoded, ':')) {
                    [$username, $password] = explode(':', $decoded, 2);
                }
            }
        }
        if (!is_string($username) || !hash_equals('review', $username) ||
            !is_string($password) || strlen($password) > 256 ||
            !password_verify($password, $found[1])) {
            self::deny(401);
        }
        header('Cache-Control: no-store, private');
    }

    private static function deny(int $status): never
    {
        http_response_code($status);
        header('X-Robots-Tag: noindex, nofollow, noarchive');
        header('Cache-Control: no-store, private');
        if ($status === 401) header('WWW-Authenticate: Basic realm="CELIKOM private review", charset="UTF-8"');
        header('Content-Type: text/plain; charset=utf-8');
        echo $status === 401 ? 'Требуется пароль закрытого стенда CELIKOM.' : 'Закрытый стенд CELIKOM недоступен.';
        exit;
    }
}
