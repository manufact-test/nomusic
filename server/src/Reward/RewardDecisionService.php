<?php

declare(strict_types=1);

namespace Celikom\Reward;

use PDO;

/** Creates capped discount credits. Payment application is a separate future operation. */
final class RewardDecisionService
{
    public function __construct(private readonly PDO $pdo) {}

    public function decide(int $adminId,int $id,int $expectedVersion,int $expectedPolicyVersion,string $action,string $reason):void
    {
        if ($id<1 || $expectedVersion<1 || !in_array($action,['approve','reject','revoke','expire'],true)
            || trim($reason)==='' || mb_strlen($reason)>500) throw new \InvalidArgumentException('invalid_reward_decision');
        $this->pdo->beginTransaction();
        try {
            RewardPolicyService::owner($this->pdo,$adminId);
            // Global policy first, then account, track, replacement and credit.
            // Moderation locks track/replacement before inserting contribution evidence.
            $policy=$this->pdo->query('SELECT * FROM reward_policy WHERE id=1 FOR UPDATE')->fetch(PDO::FETCH_ASSOC);
            $q=$this->pdo->prepare('SELECT user_id,replacement_id FROM reward_ledger WHERE id=?');$q->execute([$id]);
            $identity=$q->fetch(PDO::FETCH_ASSOC);
            if (!$identity) throw new \DomainException('reward_missing');
            $q=$this->pdo->prepare('SELECT u.status,e.verified_at FROM users u LEFT JOIN user_email_security e ON e.user_id=u.id WHERE u.id=? FOR UPDATE');
            $q->execute([$identity['user_id']]);$user=$q->fetch(PDO::FETCH_ASSOC);
            $q=$this->pdo->prepare('SELECT track_id FROM track_replacements WHERE id=?');$q->execute([$identity['replacement_id']]);$track=$q->fetchColumn();
            $q=$this->pdo->prepare('SELECT id FROM tracks WHERE id=? FOR UPDATE');$q->execute([$track]);
            $q=$this->pdo->prepare('SELECT * FROM track_replacements WHERE id=? FOR UPDATE');$q->execute([$identity['replacement_id']]);$replacement=$q->fetch(PDO::FETCH_ASSOC);
            $q=$this->pdo->prepare('SELECT *, (expires_at<=UTC_TIMESTAMP(6)) AS is_expired FROM reward_ledger WHERE id=? FOR UPDATE');$q->execute([$id]);$before=$q->fetch(PDO::FETCH_ASSOC);
            if (!$before || (int)$before['version']!==$expectedVersion) throw new \DomainException('stale_reward_decision');
            if ($action==='approve') {
                if (!$policy || !(int)$policy['enabled']) throw new \DomainException('reward_policy_disabled');
                if ((int)$policy['version']!==$expectedPolicyVersion) throw new \DomainException('stale_reward_policy');
                if ($before['status']!=='pending') throw new \DomainException('reward_not_pending');
                if (!$user || $user['status']!=='active' || $user['verified_at']===null || !$replacement
                    || $replacement['status']!=='approved' || !(int)$replacement['is_active'] || $replacement['disabled_at']!==null
                    || (int)$replacement['uploaded_by_user_id']!==(int)$before['user_id']
                    || (int)$replacement['audio_asset_id']!==(int)$before['audio_asset_id']) throw new \DomainException('reward_contribution_unavailable');
                // Moscow calendar-month cap counts all grants, even subsequently revoked/expired.
                // Current read: owner validation may have established an earlier
                // REPEATABLE READ snapshot before waiting for the policy lock.
                $q=$this->pdo->prepare("SELECT id FROM reward_ledger WHERE user_id=?
                    AND granted_at>=DATE_SUB(DATE_FORMAT(DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 3 HOUR),'%Y-%m-01'),INTERVAL 3 HOUR)
                    AND granted_at<DATE_ADD(DATE_SUB(DATE_FORMAT(DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 3 HOUR),'%Y-%m-01'),INTERVAL 3 HOUR),INTERVAL 1 MONTH) FOR UPDATE");
                $q->execute([$before['user_id']]);
                if (count($q->fetchAll(PDO::FETCH_COLUMN))>=(int)$policy['max_reward_per_month']) throw new \DomainException('reward_monthly_limit');
                $this->pdo->prepare("UPDATE reward_ledger SET status='approved',discount_percent=?,granted_at=UTC_TIMESTAMP(6),
                    expires_at=DATE_ADD(UTC_TIMESTAMP(6),INTERVAL ? DAY),policy_version=?,decided_by_admin_id=?,version=version+1 WHERE id=?")
                    ->execute([(int)$policy['upload_discount_percent'],(int)$policy['validity_days'],(int)$policy['version'],$adminId,$id]);
            } else {
                $required=$action==='reject'?'pending':'approved';
                if ($before['status']!==$required) throw new \DomainException('reward_state_conflict');
                if ($action==='expire' && !(bool)$before['is_expired']) throw new \DomainException('reward_not_expired');
                $status=$action==='expire'?'expired':'rejected';
                $this->pdo->prepare('UPDATE reward_ledger SET status=?,decided_by_admin_id=?,version=version+1 WHERE id=?')
                    ->execute([$status,$adminId,$id]);
            }
            $q=$this->pdo->prepare('SELECT * FROM reward_ledger WHERE id=?');$q->execute([$id]);$after=$q->fetch(PDO::FETCH_ASSOC);
            unset($before['is_expired']);
            RewardPolicyService::audit($this->pdo,$adminId,'reward_'.$action,'reward_ledger',$id,$reason,$before,$after);
            $this->pdo->commit();
        } catch(\Throwable $error) {
            if($this->pdo->inTransaction()) $this->pdo->rollBack();throw $error;
        }
    }
}
