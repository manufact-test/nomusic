<?php

declare(strict_types=1);

namespace Celikom\Reward;

use PDO;

/** Approval awards the full credit once. Overflow waits, expiry starts at payment. */
final class AutomaticRewardService
{
    public function __construct(private readonly PDO $pdo) {}

    public function grant(int $rewardId, int $adminId, array $policy): void
    {
        if (!$this->pdo->inTransaction()) throw new \LogicException('automatic_reward_requires_transaction');
        if (!(int)$policy['enabled']) return;
        $q=$this->pdo->prepare('SELECT * FROM reward_ledger WHERE id=? FOR UPDATE');$q->execute([$rewardId]);
        $credit=$q->fetch(PDO::FETCH_ASSOC);
        if (!$credit || $credit['status']!=='pending') return;
        // The caller has locked policy before catalog. Serialize all rewards for this account.
        $q=$this->pdo->prepare('SELECT id FROM users WHERE id=? FOR UPDATE');$q->execute([$credit['user_id']]);
        if (!$q->fetchColumn()) throw new \DomainException('reward_account_missing');
        $cap=(int)$policy['max_discount_percent'];$remaining=(int)$policy['upload_discount_percent'];
        $now=$this->pdo->query('SELECT UTC_TIMESTAMP(6)')->fetchColumn();
        $month=new \DateTimeImmutable(substr($now,0,7).'-01',new \DateTimeZone('UTC'));
        // Current read, not a repeatable-read snapshot preceding a competing approval.
        $q=$this->pdo->prepare("SELECT a.available_from,a.discount_percent FROM reward_allocations a
            JOIN reward_ledger l ON l.id=a.reward_id WHERE l.user_id=? AND l.status IN ('approved','used') FOR UPDATE");
        $q->execute([$credit['user_id']]);$reserved=[];
        foreach($q->fetchAll(PDO::FETCH_ASSOC) as $allocation) {
            $key=$allocation['available_from'];$reserved[$key]=($reserved[$key]??0)+(int)$allocation['discount_percent'];
        }
        $insert=$this->pdo->prepare('INSERT INTO reward_allocations(reward_id,part_index,available_from,discount_percent,monthly_cap_percent,validity_days) VALUES(?,?,?,?,?,?)');
        $part=0;$schedule=[];
        while($remaining>0) {
            $date=$month->format('Y-m-d');$space=max(0,$cap-($reserved[$date]??0));
            if($space>0) {
                $amount=min($space,$remaining);$insert->execute([$rewardId,++$part,$date,$amount,$cap,(int)$policy['validity_days']]);
                $schedule[]=['month'=>$date,'percent'=>$amount];$remaining-=$amount;
            }
            $month=$month->modify('+1 month');
        }
        $this->pdo->prepare("UPDATE reward_ledger SET status='approved',grant_mode='automatic',discount_percent=?,granted_at=?,
            expires_at=NULL,policy_version=?,decided_by_admin_id=?,version=version+1 WHERE id=?")
            ->execute([(int)$policy['upload_discount_percent'],$now,(int)$policy['version'],$adminId,$rewardId]);
        RewardPolicyService::audit($this->pdo,$adminId,'reward_auto_granted','reward_ledger',$rewardId,
            'Автоматически после одобрения версии песни',['status'=>'pending'],
            ['status'=>'approved','percent'=>(int)$policy['upload_discount_percent'],'allocations'=>$schedule,'validity_days'=>(int)$policy['validity_days'],'expiry_starts'=>'payment']);
    }
}
