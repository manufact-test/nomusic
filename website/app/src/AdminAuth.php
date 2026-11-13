<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use PDO;
use RuntimeException;

/**
 * Stage 9 owner-only CMS sign-in. Persistent per-IP AND per-username throttling
 * with database row locks protects parallel attempts. Never log passwords,
 * submitted usernames or unkeyed IPs. A login does not publish site content.
 */
final class AdminAuth
{
    private const WINDOW = 900;
    private const MAX_FAILURES = 5;

    /**
     * @return int|null Admin ID on success, null on any authentication failure.
     */
    public static function authenticate(
        PDO $pdo,
        string $username,
        string $password,
        string $ip,
        string $hmacKey,
        int $now
    ): ?int {
        if (strlen($hmacKey) < 32 || $ip === '' || strlen($ip) > 64 ||
            preg_match('/[\x00-\x1F\x7F]/', $ip) ||
            !filter_var($ip, FILTER_VALIDATE_IP)) {
            throw new RuntimeException('Invalid authentication server configuration');
        }
        // Uniform rejection for unknown users and malformed credentials;
        // do not expose different errors or usernames to the caller.
        if (strlen($username) < 1 || strlen($username) > 80 ||
            !preg_match('/^[A-Za-z0-9_.-]+$/D', $username) ||
            $password === '' || strlen($password) > 4096) {
            return null;
        }
        $user = strtolower($username);
        $keys = [
            hash_hmac('sha256', 'ip|' . $ip, $hmacKey),
            hash_hmac('sha256', 'user|' . $user, $hmacKey),
        ];
        sort($keys, SORT_STRING);
        $instant = gmdate('Y-m-d H:i:s', $now);
        $resetAt = gmdate('Y-m-d H:i:s', $now + self::WINDOW);
        try {
            $pdo->beginTransaction();
            foreach ($keys as $key) {
                $create = $pdo->prepare(
                    'INSERT IGNORE INTO login_rate_limits ' .
                    '(bucket_hash,attempts,window_started_at,locked_until) VALUES (?,0,?,NULL)'
                );
                $create->execute([$key, $instant]);
            }
            $read = $pdo->prepare(
                'SELECT attempts,window_started_at,locked_until FROM login_rate_limits ' .
                'WHERE bucket_hash=? FOR UPDATE'
            );
            $locked = false;
            foreach ($keys as $key) {
                $read->execute([$key]);
                $row = $read->fetch(PDO::FETCH_ASSOC);
                if (!$row) throw new RuntimeException('Missing rate-limit record');
                if ($row['locked_until'] !== null && $row['locked_until'] > $instant) {
                    $locked = true;
                }
            }
            $find = $pdo->prepare('SELECT id,password_hash,is_active FROM admin_users WHERE username=? LIMIT 1');
            $find->execute([$username]);
            $admin = $find->fetch(PDO::FETCH_ASSOC);
            // Unknown-user path also executes a password hash verification.
            $dummy = password_hash('nonexistent-celikom-admin', PASSWORD_BCRYPT, ['cost'=>10]);
            $verified = password_verify($password, $admin ? (string)$admin['password_hash'] : $dummy);
            $success = !$locked && $admin && (int)$admin['is_active'] === 1 && $verified;
            if ($success) {
                $clear = $pdo->prepare(
                    'UPDATE login_rate_limits SET attempts=0,window_started_at=?,locked_until=NULL WHERE bucket_hash=?'
                );
                // Clear only the named account bucket; keep IP brute force
                // history intact until the time window expires.
                $clear->execute([$instant,hash_hmac('sha256','user|'.$user,$hmacKey)]);
                $pdo->prepare('UPDATE admin_users SET last_login_at=? WHERE id=?')
                    ->execute([$instant,(int)$admin['id']]);
            } elseif (!$locked) {
                $update = $pdo->prepare(
                    'UPDATE login_rate_limits SET attempts=?,window_started_at=?,locked_until=? WHERE bucket_hash=?'
                );
                foreach ($keys as $key) {
                    $read->execute([$key]);
                    $row = $read->fetch(PDO::FETCH_ASSOC);
                    $windowStart = strtotime((string)$row['window_started_at'].' UTC');
                    $fresh = $windowStart === false || $now - $windowStart >= self::WINDOW;
                    $count = ($fresh ? 0 : (int)$row['attempts']) + 1;
                    $until = $count >= self::MAX_FAILURES ? $resetAt : null;
                    $update->execute([$count,$fresh ? $instant : $row['window_started_at'],$until,$key]);
                }
            }
            $audit = $pdo->prepare(
                'INSERT INTO audit_log (actor_admin_id,event_name,subject_key,event_metadata,occurred_at)' .
                ' VALUES (?,?,?,?,?)'
            );
            $audit->execute([
                $success ? (int)$admin['id'] : null,
                $success ? 'cms.login.ok' : 'cms.login.denied',
                hash_hmac('sha256','user|'.$user,$hmacKey),
                null,
                $instant,
            ]);
            $pdo->commit();
            return $success ? (int)$admin['id'] : null;
        } catch (\Throwable $exception) {
            if ($pdo->inTransaction()) $pdo->rollBack();
            throw $exception;
        }
    }

    public static function checkSession(PDO $pdo, int $now): ?int
    {
        if (session_status() !== PHP_SESSION_ACTIVE) return null;
        $id = $_SESSION['cms_admin_id'] ?? null;
        $last = $_SESSION['last_seen_at'] ?? null;
        $start = $_SESSION['authenticated_at'] ?? null;
        if (!is_int($id) || $id < 1 || !is_int($last) || !is_int($start) ||
            $last > $now + 60 || $start > $now + 60 ||
            $now - $last > 1800 || $now - $start > 43200) {
            unset($_SESSION['cms_admin_id'],$_SESSION['last_seen_at'],$_SESSION['authenticated_at']);
            return null;
        }
        $query = $pdo->prepare('SELECT id FROM admin_users WHERE id=? AND is_active=1 LIMIT 1');
        $query->execute([$id]);
        if ($query->fetchColumn() === false) {
            unset($_SESSION['cms_admin_id'],$_SESSION['last_seen_at'],$_SESSION['authenticated_at']);
            return null;
        }
        $_SESSION['last_seen_at'] = $now;
        return $id;
    }

    public static function finishLogin(int $adminId): void
    {
        if ($adminId < 1) throw new InvalidArgumentException('Invalid administrator ID');
        Security::afterLogin();
        $_SESSION['cms_admin_id'] = $adminId;
    }
}
