<?php
declare(strict_types=1);
namespace Celikom\Website;

use RuntimeException;

/**
 * Minimal shared primitives for the future protected content CMS.
 * No real login, rate limiting, role checks or admin routes exist at Stage 3.
 */
final class Security
{
    public static function startAdminSession(bool $https): void
    {
        if (!$https) {
            throw new RuntimeException('Admin sessions require HTTPS');
        }
        if (session_status() === PHP_SESSION_ACTIVE) {
            return;
        }
        if (headers_sent()) {
            throw new RuntimeException('Session headers have already been sent');
        }
        ini_set('session.use_strict_mode', '1');
        ini_set('session.use_only_cookies', '1');
        ini_set('session.cookie_httponly', '1');
        session_name('celikom_site_admin');
        session_set_cookie_params([
            'lifetime' => 0,
            'path' => '/admin/',
            'secure' => true,
            'httponly' => true,
            'samesite' => 'Lax',
        ]);
        if (session_start() !== true) {
            throw new RuntimeException('Could not start secure session');
        }
    }

    public static function afterLogin(): void
    {
        if (session_status() !== PHP_SESSION_ACTIVE || !session_regenerate_id(true)) {
            throw new RuntimeException('Cannot rotate session ID');
        }
        $_SESSION['authenticated_at'] = time();
        $_SESSION['last_seen_at'] = time();
        unset($_SESSION['csrf_token']);
    }

    public static function csrfToken(): string
    {
        self::requireSession();
        if (!isset($_SESSION['csrf_token'])) {
            $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
        }
        return (string) $_SESSION['csrf_token'];
    }

    public static function verifyCsrf(mixed $submitted): bool
    {
        self::requireSession();
        return is_string($submitted)
            && isset($_SESSION['csrf_token'])
            && hash_equals((string) $_SESSION['csrf_token'], $submitted);
    }

    public static function clearSession(): void
    {
        self::requireSession();
        $_SESSION = [];
        if (ini_get('session.use_cookies')) {
            $cookie = session_get_cookie_params();
            setcookie(session_name(), '', [
                'expires' => time() - 3600,
                'path' => $cookie['path'],
                'secure' => $cookie['secure'],
                'httponly' => $cookie['httponly'],
                'samesite' => $cookie['samesite'] ?? 'Lax',
            ]);
        }
        session_destroy();
    }

    private static function requireSession(): void
    {
        if (session_status() !== PHP_SESSION_ACTIVE) {
            throw new RuntimeException('No active admin session');
        }
    }
}
