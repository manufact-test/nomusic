<?php

declare(strict_types=1);

namespace Celikom\Referral;

use PDO;

/** Immutable registration attribution. No client-controlled paid qualification. */
final class ReferralService
{
    public function __construct(private readonly PDO $pdo) {}

    public function code(int $userId): string
    {
        if ($this->pdo->inTransaction()) throw new \LogicException('nested_referral_transaction');
        $this->pdo->beginTransaction();
        try {
            $q=$this->pdo->prepare("SELECT u.id FROM users u JOIN user_email_security e ON e.user_id=u.id
                WHERE u.id=? AND u.status='active' AND e.verified_at IS NOT NULL FOR UPDATE");
            $q->execute([$userId]);
            if (!$q->fetchColumn()) throw new \DomainException('invalid_session');
            $q=$this->pdo->prepare('SELECT code FROM referral_codes WHERE user_id=? FOR UPDATE');
            $q->execute([$userId]);$code=$q->fetchColumn();
            if (!is_string($code)) {
                $code=strtoupper(bin2hex(random_bytes(16)));
                $this->pdo->prepare('INSERT INTO referral_codes(user_id,code) VALUES(?,?)')->execute([$userId,$code]);
            }
            $this->pdo->commit();return $code;
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }

    public function validate(string $code): void
    {
        if (!preg_match('/^[A-F0-9]{32}$/D',$code)) throw new \DomainException('invalid_referral_code');
        $q=$this->pdo->prepare("SELECT c.user_id FROM referral_codes c JOIN users u ON u.id=c.user_id
            JOIN user_email_security e ON e.user_id=u.id WHERE c.code=? AND u.status='active' AND e.verified_at IS NOT NULL");
        $q->execute([$code]);if (!$q->fetchColumn()) throw new \DomainException('invalid_referral_code');
    }

    /** Only called inside the transaction creating a new, still invisible user. */
    public function bindRegistration(int $newUserId, string $code): void
    {
        if (!$this->pdo->inTransaction()) throw new \LogicException('registration_transaction_required');
        $this->validate($code);
        $q=$this->pdo->prepare("SELECT c.user_id FROM referral_codes c JOIN users u ON u.id=c.user_id
            JOIN user_email_security e ON e.user_id=u.id WHERE c.code=? AND u.status='active'
                AND e.verified_at IS NOT NULL FOR UPDATE");
        $q->execute([$code]);$referrer=(int)$q->fetchColumn();
        if (!$referrer || $referrer===$newUserId) throw new \DomainException('invalid_referral_code');
        $q=$this->pdo->prepare('SELECT referrer_user_id FROM referrals WHERE invited_user_id=? FOR UPDATE');
        $q->execute([$newUserId]);$existing=$q->fetchColumn();
        if ($existing!==false) {
            if ((int)$existing!==$referrer) throw new \DomainException('referral_already_bound');
            return;
        }
        $this->pdo->prepare('INSERT INTO referrals(referrer_user_id,invited_user_id) VALUES(?,?)')->execute([$referrer,$newUserId]);
    }

    public function summary(int $userId): array
    {
        $q=$this->pdo->prepare('SELECT code FROM referral_codes WHERE user_id=?');$q->execute([$userId]);
        $code=$q->fetchColumn();
        $q=$this->pdo->prepare('SELECT COUNT(*) FROM referrals WHERE referrer_user_id=?');$q->execute([$userId]);
        return ['code'=>is_string($code) ? $code : null,'registered_count'=>(int)$q->fetchColumn(),
            'qualified_count'=>0,'qualification_available'=>false,'discount_active'=>false,
            'reward_available'=>false,'share_url'=>null];
    }
}
