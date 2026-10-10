<?php

declare(strict_types=1);

namespace Celikom\Entitlement;

use PDO;

/** Explicit activation only; registration/login/read-only checks never start a trial. */
final class TrialService
{
    public function __construct(private readonly PDO $pdo) {}

    public function activate(int $userId): array
    {
        // Never commit or roll back a transaction owned by another service.
        if ($this->pdo->inTransaction()) throw new \LogicException('trial_transaction_already_open');
        $this->pdo->beginTransaction();
        try {
            // Lock the parent: it exists before either device can create the trial row.
            $select = $this->pdo->prepare('SELECT id, status FROM users WHERE id = ? FOR UPDATE');
            $select->execute([$userId]);
            $user = $select->fetch(PDO::FETCH_ASSOC);
            if (!$user) throw new \DomainException('user_not_found');
            if ($user['status'] !== 'active') throw new \DomainException('account_disabled');
            $verified = $this->pdo->prepare('SELECT verified_at FROM user_email_security WHERE user_id = ? FOR UPDATE');
            $verified->execute([$userId]);
            if (!$verified->fetchColumn()) throw new \DomainException('email_unverified');

            $trial = $this->pdo->prepare('SELECT valid_from, valid_until FROM account_trials WHERE user_id = ?');
            $trial->execute([$userId]);
            $existing = $trial->fetch(PDO::FETCH_ASSOC);
            if ($existing) {
                $this->pdo->commit();
                return self::result(false, $existing);
            }

            // One database-clock sample, with full DATETIME(6) precision.
            $window = $this->pdo->query('SELECT UTC_TIMESTAMP(6) AS valid_from,
                DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 432000 SECOND) AS valid_until')->fetch(PDO::FETCH_ASSOC);
            $ledgerId = (new EntitlementLedger($this->pdo))
                ->recordTrial($userId, $window['valid_from'], $window['valid_until']);
            $insert = $this->pdo->prepare('INSERT INTO account_trials (user_id, ledger_id, valid_from, valid_until)
                VALUES (?, ?, ?, ?)');
            $insert->execute([$userId, $ledgerId, $window['valid_from'], $window['valid_until']]);
            $this->pdo->commit();
            return self::result(true, $window);
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }

    private static function result(bool $activated, array $window): array
    {
        return ['activated' => $activated, 'trial_seconds' => 432000,
            'trial_started_at' => EntitlementResult::utc($window['valid_from']),
            'trial_ends_at' => EntitlementResult::utc($window['valid_until'])];
    }
}
