<?php
declare(strict_types=1);
namespace Celikom\Auth;

/** Email is the ownership proof; installation UUID is only a session identifier. */
final class EmailFlow
{
    private readonly SmtpMailer $mail;
    public function __construct(private readonly \PDO $db, private readonly array $config)
    {
        $this->mail = new SmtpMailer($config);
    }
    public function ready(): bool
    {
        return $this->mail->ready() && strlen((string)($this->config['mail_code_pepper'] ?? '')) >= 32;
    }
    private function guardReady(): void
    {
        if (!$this->ready()) throw new \DomainException('email_unavailable');
    }
    private function digest(int $id, string $code, string $scope): string
    {
        return hash_hmac('sha256', $id.':'.$scope.':'.$code, (string)$this->config['mail_code_pepper']);
    }
    private function code(): string { return str_pad((string)random_int(0,999999), 6, '0', STR_PAD_LEFT); }
    public function isVerified(int $id): bool
    {
        $s=$this->db->prepare('SELECT COUNT(*) FROM user_email_security WHERE user_id=? AND verified_at IS NOT NULL');
        $s->execute([$id]);
        return (int)$s->fetchColumn()===1;
    }
    public function sendVerification(int $id,string $email): array
    {
        $this->guardReady();
        $this->db->prepare('INSERT IGNORE INTO user_email_security (user_id) VALUES (?)')->execute([$id]);
        $s=$this->db->prepare('SELECT verified_at,verification_sent_at
            FROM user_email_security WHERE user_id=?');
        $s->execute([$id]);
        $row=$s->fetch(\PDO::FETCH_ASSOC);
        if (!$row || $row['verified_at'] !== null) throw new \DomainException('invalid_request');
        if ($row['verification_sent_at']!==null && strtotime($row['verification_sent_at'].' UTC')>time()-60) {
            return ['verification_required'=>true,'email'=>$email];
        }
        $code=$this->code();
        $hash=$this->digest($id,$code,'verify');
        $update=$this->db->prepare('UPDATE user_email_security
          SET verification_hash=?,verification_expires_at=DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 10 MINUTE),
              verification_attempts=0,verification_sent_at=UTC_TIMESTAMP(6)
          WHERE user_id=? AND verified_at IS NULL');
        $update->execute([$hash,$id]);
        if ($update->rowCount()!==1) throw new \DomainException('invalid_request');
        try { $this->mail->sendCode($email,$code,'verify'); }
        catch (\Throwable) {
            $this->db->prepare('UPDATE user_email_security
              SET verification_hash=NULL,verification_sent_at=NULL,verification_expires_at=NULL
              WHERE user_id=? AND verification_hash=?')->execute([$id,$hash]);
            throw new \DomainException('email_unavailable');
        }
        return ['verification_required'=>true,'email'=>$email];
    }
    public function verifyEmail(int $id,string $code): void
    {
        if (!preg_match('/^[0-9]{6}$/D',$code)) throw new \DomainException('invalid_code');
        $hash=$this->digest($id,$code,'verify');
        $s=$this->db->prepare('UPDATE user_email_security
            SET verified_at=UTC_TIMESTAMP(6),verification_hash=NULL,verification_expires_at=NULL,
                verification_sent_at=NULL,verification_attempts=0
            WHERE user_id=? AND verified_at IS NULL AND verification_hash=?
              AND verification_expires_at > UTC_TIMESTAMP(6) AND verification_attempts < 5');
        $s->execute([$id,$hash]);
        if ($s->rowCount()!==1) {
            $this->db->prepare('UPDATE user_email_security
                SET verification_attempts=LEAST(5,verification_attempts+1)
                WHERE user_id=? AND verified_at IS NULL AND verification_hash IS NOT NULL
                  AND verification_expires_at > UTC_TIMESTAMP(6)')->execute([$id]);
            throw new \DomainException('invalid_code');
        }
    }
    public function throttle(string $kind,string $identity,string $ip,int $limit=5): void
    {
        $window=intdiv(time(),900);
        foreach (["mail-$kind:$identity","mail-$kind-ip:$ip"] as $key) {
            $hash=hash('sha256',$key);
            $this->db->prepare('INSERT INTO user_auth_attempts (identity_hash,window_start,attempts)
                VALUES (?, ?, 1) ON DUPLICATE KEY UPDATE attempts=attempts+1')->execute([$hash,$window]);
            $s=$this->db->prepare('SELECT attempts FROM user_auth_attempts WHERE identity_hash=? AND window_start=?');
            $s->execute([$hash,$window]);
            if ((int)$s->fetchColumn()>($key==="mail-$kind:$identity"?$limit:30))
                throw new \DomainException('rate_limited');
        }
    }
    public function requestReset(string $email,string $ip): array
    {
        $this->guardReady();
        $this->throttle('reset',$email,$ip,5);
        $s=$this->db->prepare('SELECT u.id,e.verified_at,e.reset_sent_at
          FROM users u LEFT JOIN user_email_security e ON e.user_id=u.id
          WHERE u.email=? AND u.status=? LIMIT 1');
        $s->execute([$email,'active']);
        $user=$s->fetch(\PDO::FETCH_ASSOC);
        $message=['ok'=>true];
        if (!$user) return $message;
        $id=(int)$user['id'];
        $this->db->prepare('INSERT IGNORE INTO user_email_security (user_id) VALUES (?)')->execute([$id]);
        if ($user['reset_sent_at']!==null && strtotime($user['reset_sent_at'].' UTC')>time()-60)
            return $message;
        $code=$this->code();
        $hash=$this->digest($id,$code,'reset');
        $this->db->prepare('UPDATE user_email_security
          SET reset_hash=?,reset_expires_at=DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 10 MINUTE),
              reset_attempts=0,reset_sent_at=UTC_TIMESTAMP(6) WHERE user_id=?')
            ->execute([$hash,$id]);
        try { $this->mail->sendCode($email,$code,'reset'); }
        catch (\Throwable) {
            $this->db->prepare('UPDATE user_email_security
              SET reset_hash=NULL,reset_sent_at=NULL,reset_expires_at=NULL
              WHERE user_id=? AND reset_hash=?')->execute([$id,$hash]);
            // Reset responses must remain indistinguishable for existing and
            // missing mailboxes even if their SMTP delivery fails.
            return $message;
        }
        return $message;
    }
    public function resetPassword(string $email,string $code,string $passwordHash): array
    {
        if (!preg_match('/^[0-9]{6}$/D',$code)) throw new \DomainException('invalid_code');
        $this->db->beginTransaction();
        try {
            $s=$this->db->prepare('SELECT u.id,e.verified_at,e.reset_hash,e.reset_expires_at,e.reset_attempts
                FROM users u JOIN user_email_security e ON e.user_id=u.id
                WHERE u.email=? AND u.status=? FOR UPDATE');
            $s->execute([$email,'active']);
            $row=$s->fetch(\PDO::FETCH_ASSOC);
            $valid=$row && $row['reset_hash']!==null
                && (int)$row['reset_attempts']<5
                && strtotime($row['reset_expires_at'].' UTC')>time()
                && hash_equals((string)$row['reset_hash'],$this->digest((int)$row['id'],$code,'reset'));
            if (!$valid) {
                if ($row && $row['reset_hash']!==null) {
                    $this->db->prepare('UPDATE user_email_security
                      SET reset_attempts=LEAST(5,reset_attempts+1) WHERE user_id=?')
                      ->execute([$row['id']]);
                }
                $this->db->commit();
                throw new \DomainException('invalid_code');
            }
            $this->db->prepare('UPDATE users SET password_hash=? WHERE id=?')->execute([$passwordHash,$row['id']]);
            $this->db->prepare('UPDATE user_sessions SET revoked_at=UTC_TIMESTAMP(6)
                WHERE user_id=? AND revoked_at IS NULL')->execute([$row['id']]);
            $this->db->prepare('UPDATE user_email_security
                SET verified_at=COALESCE(verified_at,UTC_TIMESTAMP(6)),
                    reset_hash=NULL,reset_expires_at=NULL,reset_sent_at=NULL,reset_attempts=0,
                    verification_hash=NULL,verification_expires_at=NULL,verification_sent_at=NULL,
                    verification_attempts=0 WHERE user_id=?')
                ->execute([$row['id']]);
            $this->db->commit();
            return ['ok'=>true];
        } catch (\Throwable $e) {
            if($this->db->inTransaction())$this->db->rollBack();
            throw $e;
        }
    }
}
