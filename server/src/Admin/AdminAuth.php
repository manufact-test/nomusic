<?php

declare(strict_types=1);

namespace Celikom\Admin;

/** Closed, server-side admin identity: no public signup and no extension tokens. */
final class AdminAuth
{
    public const COOKIE = '__Host-celikom_admin';
    public const LOGIN_COOKIE = '__Host-celikom_login';

    public function __construct(private readonly \PDO $pdo) {}

    public static function cookie(string $name, string $value, int $maxAge): string
    {
        return $name . '=' . rawurlencode($value) . '; Path=/; Max-Age=' . $maxAge
            . '; Secure; HttpOnly; SameSite=Strict';
    }

    public static function readCookie(array $headers, string $name): string
    {
        $cookie = (string) ($headers['cookie'] ?? '');
        foreach (explode(';', $cookie) as $item) {
            $pair = explode('=', trim($item), 2);
            if (count($pair) === 2 && $pair[0] === $name) {
                return rawurldecode($pair[1]);
            }
        }
        return '';
    }

    public static function csrfForToken(string $token): string
    {
        return hash_hmac('sha256', 'celikom-admin-csrf-v1', $token);
    }

    /** @return array{id:int,role:string,login:string,csrf:string}|null */
    public function authenticate(array $headers): ?array
    {
        $token = self::readCookie($headers, self::COOKIE);
        if (!preg_match('/^[a-f0-9]{64}$/D', $token)) return null;
        $stmt = $this->pdo->prepare('SELECT a.id, a.role, a.login, s.csrf_hash
            FROM admin_sessions s JOIN admins a ON a.id = s.admin_id
            WHERE s.token_hash = ? AND s.expires_at > UTC_TIMESTAMP(6) AND a.enabled = 1 LIMIT 1');
        $stmt->execute([hash('sha256', $token)]);
        $row = $stmt->fetch(\PDO::FETCH_ASSOC);
        if (!$row) return null;
        $csrf = self::csrfForToken($token);
        if (!hash_equals((string) $row['csrf_hash'], hash('sha256', $csrf))) return null;
        return ['id' => (int) $row['id'], 'role' => (string) $row['role'],
            'login' => (string) $row['login'], 'csrf' => $csrf];
    }

    /** @return array{token:string}|null */
    public function login(string $login, string $password, string $remoteAddress): ?array
    {
        if (strlen($login) > 120 || strlen($password) > 4096 || !preg_match('/^[a-zA-Z0-9_.-]{3,120}$/D', $login)) {
            return null;
        }
        // Bound both the login/IP pair and IP alone; retain no raw IP addresses.
        $window = (int) (floor(time() / 900) * 900);
        $keys = [hash('sha256', 'login|' . strtolower($login) . '|' . $remoteAddress),
            hash('sha256', 'ip|' . $remoteAddress)];
        $inc = $this->pdo->prepare('INSERT INTO admin_login_attempts (identity_hash, window_start, attempts)
            VALUES (?, ?, 1) ON DUPLICATE KEY UPDATE attempts = attempts + 1');
        $count = $this->pdo->prepare('SELECT attempts FROM admin_login_attempts
            WHERE identity_hash = ? AND window_start = ?');
        foreach ($keys as $i => $key) {
            $inc->execute([$key, $window]);
            $count->execute([$key, $window]);
            if ((int) $count->fetchColumn() > ($i === 0 ? 8 : 30)) return null;
        }
        $lookup = $this->pdo->prepare('SELECT id, password_hash FROM admins WHERE login = ? AND enabled = 1');
        $lookup->execute([$login]);
        $admin = $lookup->fetch(\PDO::FETCH_ASSOC);
        if (!$admin || !password_verify($password, (string) $admin['password_hash'])) return null;
        $token = bin2hex(random_bytes(32));
        $csrf = self::csrfForToken($token);
        $this->pdo->prepare('INSERT INTO admin_sessions (token_hash, admin_id, csrf_hash, expires_at)
            VALUES (?, ?, ?, DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 6 HOUR))')
            ->execute([hash('sha256', $token), (int) $admin['id'], hash('sha256', $csrf)]);
        $this->pdo->prepare('UPDATE admins SET last_login_at = UTC_TIMESTAMP(6) WHERE id = ?')
            ->execute([(int) $admin['id']]);
        return ['token' => $token];
    }

    public function logout(array $headers): void
    {
        $token = self::readCookie($headers, self::COOKIE);
        if (preg_match('/^[a-f0-9]{64}$/D', $token)) {
            $this->pdo->prepare('DELETE FROM admin_sessions WHERE token_hash = ?')
                ->execute([hash('sha256', $token)]);
        }
    }

    public static function validCsrf(?array $admin, mixed $submitted): bool
    {
        return $admin !== null && is_string($submitted)
            && strlen($submitted) === 64 && hash_equals($admin['csrf'], $submitted);
    }
}
