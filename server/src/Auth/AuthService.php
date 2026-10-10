<?php

declare(strict_types=1);

namespace Celikom\Auth;

/**
 * Customer identity only: deliberately does not inspect admins or admin_sessions.
 * Bearer tokens are opaque CSPRNG values; only SHA-256 digests are stored.
 */
final class AuthService
{
    private const ACCESS_SECONDS = 900;
    private const REFRESH_SECONDS = 2592000;

    private readonly EmailFlow $email;

    public function __construct(private readonly \PDO $pdo, array $config = [])
    {
        $this->email = new EmailFlow($pdo, $config);
    }

    public function register(array $input, string $remoteAddress): array
    {
        [$email, $password, $installation] = $this->credentials($input);
        $this->throttle('register', $email, $remoteAddress);
        if (!$this->email->ready()) throw new \DomainException('email_unavailable');
        $passwordHash = self::strongHash($password);
        try {
            $insert = $this->pdo->prepare('INSERT INTO users (email, password_hash) VALUES (?, ?)');
            $insert->execute([$email, $passwordHash]);
        } catch (\PDOException $error) {
            if (($error->errorInfo[1] ?? null) === 1062) throw new \DomainException('account_unavailable');
            throw $error;
        }
        $userId = (int) $this->pdo->lastInsertId();
        $this->event($userId, 'user_registered');
        return $this->email->sendVerification($userId, $email);
    }

    public function login(array $input, string $remoteAddress): array
    {
        [$email, $password, $installation] = $this->credentials($input);
        $this->throttle('login', $email, $remoteAddress);
        $select = $this->pdo->prepare('SELECT id, password_hash, status FROM users WHERE email = ? LIMIT 1');
        $select->execute([$email]);
        $row = $select->fetch(\PDO::FETCH_ASSOC);
        if (!$row || !password_verify($password, (string) $row['password_hash'])) {
            throw new \DomainException('invalid_credentials');
        }
        if ($row['status'] !== 'active') throw new \DomainException('account_disabled');
        $id = (int) $row['id'];
        if (!$this->email->isVerified($id)) {
            return $this->email->sendVerification($id, $email);
        }
        $argon = defined('PASSWORD_ARGON2ID');
        $options = $argon ? ['memory_cost' => 32768, 'time_cost' => 3, 'threads' => 1] : ['cost' => 12];
        if (password_needs_rehash((string)$row['password_hash'], $argon ? PASSWORD_ARGON2ID : PASSWORD_BCRYPT, $options)) {
            $newHash = password_hash($password, $argon ? PASSWORD_ARGON2ID : PASSWORD_BCRYPT, $options);
            $this->pdo->prepare('UPDATE users SET password_hash = ? WHERE id = ?')->execute([$newHash, $id]);
        }
        $this->pdo->prepare('UPDATE users SET last_login_at = UTC_TIMESTAMP(6) WHERE id = ?')->execute([$id]);
        $this->event($id, 'login');
        return $this->newSession($id, $installation, $email);
    }

    public function refresh(array $input): array
    {
        $token = self::tokenField($input, 'refresh_token');
        $installation = self::installation($input);
        $hash = hash('sha256', $token);
        $this->pdo->beginTransaction();
        try {
            // Lock both current and immediately preceding refresh token to detect replay.
            $select = $this->pdo->prepare('SELECT s.id, s.user_id, s.refresh_hash, s.revoked_at,
                s.refresh_expires_at, u.email, u.status, d.installation_id
                FROM user_sessions s JOIN users u ON u.id = s.user_id
                JOIN user_devices d ON d.id = s.device_id
                WHERE s.refresh_hash = ? OR s.previous_refresh_hash = ? FOR UPDATE');
            $select->execute([$hash, $hash]);
            $rows = $select->fetchAll(\PDO::FETCH_ASSOC);
            if (count($rows) !== 1) throw new \DomainException('invalid_session');
            $row = $rows[0];
            if (!hash_equals((string) $row['installation_id'], $installation) || $row['revoked_at'] !== null ||
                $row['status'] !== 'active' || strtotime($row['refresh_expires_at'] . ' UTC') <= time()) {
                throw new \DomainException('invalid_session');
            }
            if (!$this->email->isVerified((int)$row['user_id'])) throw new \DomainException('invalid_session');
            if (!hash_equals((string) $row['refresh_hash'], $hash)) {
                $this->pdo->prepare('UPDATE user_sessions SET revoked_at = UTC_TIMESTAMP(6) WHERE id = ?')
                    ->execute([$row['id']]);
                $this->pdo->commit();
                throw new \DomainException('invalid_session');
            }
            [$access, $refresh] = self::issueTokens();
            $update = $this->pdo->prepare('UPDATE user_sessions
                SET previous_refresh_hash = refresh_hash, refresh_hash = ?, access_hash = ?,
                    access_expires_at = DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 900 SECOND),
                    refresh_expires_at = DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 2592000 SECOND),
                    last_refreshed_at = UTC_TIMESTAMP(6) WHERE id = ?');
            $update->execute([hash('sha256', $refresh), hash('sha256', $access), $row['id']]);
            $this->pdo->prepare('UPDATE user_devices SET last_seen_at = UTC_TIMESTAMP(6)
                WHERE user_id = ? AND installation_id = ?')->execute([$row['user_id'], $installation]);
            $this->pdo->commit();
            return $this->sessionResponse((int) $row['user_id'], (string) $row['email'], $access, $refresh);
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }

    public function me(string $accessToken): array
    {
        $row = $this->findAccess($accessToken);
        return ['user' => ['id' => (int)$row['user_id'], 'email' => $row['email'], 'status' => $row['status']]];
    }

    public function logout(array $input): array
    {
        $token = self::tokenField($input, 'refresh_token');
        $installation = self::installation($input);
        $update = $this->pdo->prepare('UPDATE user_sessions s JOIN user_devices d ON d.id = s.device_id
            SET s.revoked_at = UTC_TIMESTAMP(6)
            WHERE s.refresh_hash = ? AND d.installation_id = ? AND s.revoked_at IS NULL');
        $update->execute([hash('sha256', $token), $installation]);
        // Idempotent, no account/session enumeration.
        return ['ok' => true];
    }

    public function sessions(string $accessToken): array
    {
        $row = $this->findAccess($accessToken);
        $select = $this->pdo->prepare('SELECT s.id, d.installation_id, s.created_at, s.last_refreshed_at
            FROM user_sessions s JOIN user_devices d ON d.id = s.device_id
            WHERE s.user_id = ? AND s.revoked_at IS NULL AND s.refresh_expires_at > UTC_TIMESTAMP(6)
            ORDER BY s.created_at DESC LIMIT 100');
        $select->execute([$row['user_id']]);
        $sessions = [];
        foreach ($select->fetchAll(\PDO::FETCH_ASSOC) as $session) {
            $sessions[] = ['id' => (int)$session['id'],
                'device_id' => $session['installation_id'],
                'created_at' => $session['created_at'],
                'current' => (int)$session['id'] === (int)$row['session_id']];
        }
        return ['sessions' => $sessions];
    }

    public function revoke(string $accessToken, array $input): array
    {
        $row = $this->findAccess($accessToken);
        if (!is_int($input['session_id'] ?? null) || $input['session_id'] < 1) throw new \InvalidArgumentException();
        $update = $this->pdo->prepare('UPDATE user_sessions SET revoked_at = UTC_TIMESTAMP(6)
            WHERE id = ? AND user_id = ? AND revoked_at IS NULL');
        $update->execute([$input['session_id'], $row['user_id']]);
        return ['ok' => true];
    }

    public function activate(string $accessToken): array
    {
        $row = $this->findAccess($accessToken);
        $update = $this->pdo->prepare('UPDATE users SET first_activated_at = UTC_TIMESTAMP(6)
            WHERE id = ? AND first_activated_at IS NULL');
        $update->execute([$row['user_id']]);
        if ($update->rowCount() === 1) $this->event((int)$row['user_id'], 'first_activation');
        $this->event((int)$row['user_id'], 'celikom_started');
        // Stage 9 does not start trial or change entitlements.
        return ['ok' => true];
    }

    /** Confirmation of email is the only path that activates a new account session. */
    public function verifyEmail(array $input): array
    {
        $email = self::emailField($input);
        $code = $input['code'] ?? null;
        $installation = self::installation($input);
        if (!is_string($code)) throw new \InvalidArgumentException('invalid_code');
        $select = $this->pdo->prepare('SELECT id,status FROM users WHERE email=? LIMIT 1');
        $select->execute([$email]);
        $user = $select->fetch(\PDO::FETCH_ASSOC);
        if (!$user || $user['status']!=='active') throw new \DomainException('invalid_code');
        $this->email->verifyEmail((int)$user['id'],$code);
        return $this->newSession((int)$user['id'],$installation,$email);
    }

    public function resendVerification(array $input,string $ip): array
    {
        [$email,$password] = $this->credentials($input);
        $this->throttle('resend',$email,$ip);
        $select = $this->pdo->prepare('SELECT id,password_hash,status FROM users WHERE email=? LIMIT 1');
        $select->execute([$email]); $user=$select->fetch(\PDO::FETCH_ASSOC);
        if (!$user || $user['status']!=='active' || !password_verify($password,$user['password_hash']))
            throw new \DomainException('invalid_credentials');
        if ($this->email->isVerified((int)$user['id'])) throw new \DomainException('invalid_request');
        return $this->email->sendVerification((int)$user['id'],$email);
    }

    public function requestReset(array $input,string $ip): array
    {
        return $this->email->requestReset(self::emailField($input),$ip);
    }

    public function resetPassword(array $input): array
    {
        $email=self::emailField($input);
        $code=$input['code']??null;
        $password=$input['new_password']??null;
        if(!is_string($code)||!is_string($password))throw new \InvalidArgumentException('invalid_request');
        $hash=self::strongHash($password);
        return $this->email->resetPassword($email,$code,$hash);
    }

    private static function emailField(array $input): string
    {
        $email=$input['email']??null;
        if (!is_string($email) || strlen($email)>254 || strlen($email)<5 ||
          !filter_var($email,FILTER_VALIDATE_EMAIL)) throw new \InvalidArgumentException('invalid_email');
        return strtolower($email);
    }

    private static function strongHash(string $password): string
    {
        $count=preg_match_all('/./us',$password);
        if ($count===false || $count<12 || $count>128 || strlen($password)>512 ||
            str_contains($password,"\0") ||
            (!defined('PASSWORD_ARGON2ID') && strlen($password)>72))
            throw new \DomainException('weak_password');
        $hash=defined('PASSWORD_ARGON2ID')
            ? password_hash($password,PASSWORD_ARGON2ID,['memory_cost'=>32768,'time_cost'=>3,'threads'=>1])
            : password_hash($password,PASSWORD_BCRYPT,['cost'=>12]);
        if (!is_string($hash))throw new \RuntimeException('password_hash_failed');
        return $hash;
    }

    private function findAccess(string $token): array
    {
        if (!preg_match('/^[0-9a-f]{64}$/D', $token)) throw new \DomainException('invalid_session');
        $select = $this->pdo->prepare('SELECT s.id AS session_id, s.user_id, u.email, u.status
            FROM user_sessions s JOIN users u ON u.id = s.user_id
            WHERE s.access_hash = ? AND s.revoked_at IS NULL
              AND s.access_expires_at > UTC_TIMESTAMP(6) AND u.status = ?
              AND EXISTS (SELECT 1 FROM user_email_security e WHERE e.user_id = u.id AND e.verified_at IS NOT NULL)
              LIMIT 1');
        $select->execute([hash('sha256', $token), 'active']);
        $row = $select->fetch(\PDO::FETCH_ASSOC);
        if (!$row) throw new \DomainException('invalid_session');
        return $row;
    }

    private function newSession(int $userId, string $installation, string $email): array
    {
        if (!$this->email->isVerified($userId)) throw new \DomainException('email_unverified');
        [$access, $refresh] = self::issueTokens();
        $this->pdo->beginTransaction();
        try {
            $insert = $this->pdo->prepare('INSERT INTO user_devices (user_id, installation_id)
                VALUES (?, ?) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id), last_seen_at = UTC_TIMESTAMP(6)');
            $insert->execute([$userId, $installation]);
            $device = (int)$this->pdo->lastInsertId();
            $session = $this->pdo->prepare('INSERT INTO user_sessions
                (user_id, device_id, access_hash, refresh_hash, access_expires_at, refresh_expires_at)
                VALUES (?, ?, ?, ?, DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 900 SECOND),
                    DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 2592000 SECOND))');
            $session->execute([$userId, $device, hash('sha256',$access), hash('sha256',$refresh)]);
            $this->pdo->commit();
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
        return $this->sessionResponse($userId, $email, $access, $refresh);
    }

    private function sessionResponse(int $userId, string $email, string $access, string $refresh): array
    {
        return ['user' => ['id' => $userId, 'email' => $email, 'status' => 'active'],
            'access_token' => $access, 'refresh_token' => $refresh,
            'token_type' => 'Bearer', 'expires_in' => self::ACCESS_SECONDS];
    }

    private static function issueTokens(): array
    {
        return [bin2hex(random_bytes(32)), bin2hex(random_bytes(32))];
    }

    private function credentials(array $input): array
    {
        $email = $input['email'] ?? null;
        $password = $input['password'] ?? null;
        if (!is_string($email) || strlen($email) > 254 || strlen($email) < 5 ||
            !preg_match('/^[a-zA-Z0-9.!#$%&\x27*+\/=?^_\x60{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$/D', $email)) {
            throw new \InvalidArgumentException('invalid_email');
        }
        if (!is_string($password) || strlen($password) > 512 || str_contains($password, "\0")) {
            throw new \InvalidArgumentException('invalid_password');
        }
        return [strtolower($email), $password, self::installation($input)];
    }

    private static function installation(array $input): string
    {
        $id = $input['installation_id'] ?? null;
        if (!is_string($id) || !preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/Di', $id)) {
            throw new \InvalidArgumentException('invalid_installation_id');
        }
        return strtolower($id);
    }

    private static function tokenField(array $input, string $name): string
    {
        $token = $input[$name] ?? null;
        if (!is_string($token) || !preg_match('/^[0-9a-f]{64}$/D', $token)) {
            throw new \DomainException('invalid_session');
        }
        return $token;
    }

    private function throttle(string $action, string $email, string $ip): void
    {
        $window = intdiv(time(), 900);
        foreach ([['email:' . $action . ':' . $email, 12], ['ip:' . $action . ':' . $ip, 50]] as [$key, $limit]) {
            $hash = hash('sha256', $key);
            $insert = $this->pdo->prepare('INSERT INTO user_auth_attempts
                (identity_hash, window_start, attempts) VALUES (?, ?, 1)
                ON DUPLICATE KEY UPDATE attempts = attempts + 1');
            $insert->execute([$hash, $window]);
            $select = $this->pdo->prepare('SELECT attempts FROM user_auth_attempts
                WHERE identity_hash = ? AND window_start = ?');
            $select->execute([$hash, $window]);
            if ((int)$select->fetchColumn() > $limit) throw new \DomainException('rate_limited');
        }
    }

    private function event(int $userId, string $event): void
    {
        $statement = $this->pdo->prepare('INSERT INTO user_auth_events (user_id, event_name) VALUES (?, ?)');
        $statement->execute([$userId, $event]);
    }
}
