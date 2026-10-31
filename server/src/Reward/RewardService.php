<?php

declare(strict_types=1);

namespace Celikom\Reward;

use PDO;

/** Evidence for a future configured reward, never an entitlement or a discount. */
final class RewardService
{
    public function __construct(private readonly PDO $pdo, private readonly bool $automatic = true) {}

    public function lockPolicy(): array
    {
        if (!$this->pdo->inTransaction()) throw new \LogicException('reward_requires_moderation_transaction');
        return $this->pdo->query('SELECT * FROM reward_policy WHERE id=1 FOR UPDATE')->fetch(PDO::FETCH_ASSOC);
    }

    /** Called only inside the transaction that approves a pending upload. */
    public function recordApprovedUpload(int $replacementId, int $adminId): void
    {
        if (!$this->pdo->inTransaction()) throw new \LogicException('reward_requires_moderation_transaction');
        $policy=$this->lockPolicy();
        $q = $this->pdo->prepare('SELECT audio_asset_id FROM track_replacements WHERE id=?');
        $q->execute([$replacementId]);
        $assetId = $q->fetchColumn();
        if ($assetId === false) throw new \DomainException('reward_candidate_missing');
        // Serialize different Track IDs sharing byte-identical audio. Only the first
        // mapping's uploader can be credited; relinking/reuploading is not new work.
        $q = $this->pdo->prepare('SELECT id FROM audio_assets WHERE id=? FOR UPDATE');
        $q->execute([$assetId]);
        if (!$q->fetchColumn()) throw new \DomainException('reward_asset_missing');
        $q = $this->pdo->prepare('SELECT r.id,r.status,r.is_active,r.disabled_at,r.uploaded_by_user_id,
            r.approved_by_admin_id,r.approved_at,u.status AS account_status,e.verified_at
            FROM track_replacements r
            LEFT JOIN users u ON u.id=r.uploaded_by_user_id
            LEFT JOIN user_email_security e ON e.user_id=u.id
            WHERE r.audio_asset_id=? ORDER BY r.id ASC LIMIT 1');
        $q->execute([$assetId]);
        $row = $q->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['id'] !== $replacementId || $row['status'] !== 'approved'
            || (int)$row['is_active'] !== 1 || $row['disabled_at'] !== null
            || (int)$row['approved_by_admin_id'] !== $adminId || $row['approved_at'] === null
            || !$row['uploaded_by_user_id'] || $row['account_status'] !== 'active' || $row['verified_at'] === null) return;
        // Current read, including a previous issuer that committed while we waited
        // for the asset lock (MySQL REPEATABLE READ must not reuse an old snapshot).
        $q = $this->pdo->prepare('SELECT id FROM reward_ledger WHERE audio_asset_id=? FOR UPDATE');
        $q->execute([$assetId]);
        if ($q->fetchColumn()) return;
        $this->pdo->prepare('INSERT INTO reward_ledger(user_id,audio_asset_id,replacement_id,approved_by_admin_id)
            VALUES(?,?,?,?)')->execute([(int)$row['uploaded_by_user_id'],(int)$assetId,$replacementId,$adminId]);
        $id = (int)$this->pdo->lastInsertId();
        $this->pdo->prepare('INSERT INTO audit_log(admin_id,action,entity_type,entity_id,reason,before_json,after_json)
            VALUES(?,?,?,?,?,?,?)')->execute([$adminId,'reward_eligibility_recorded','reward_ledger',$id,
                'approved_upload_pending_reward_policy','{}',json_encode(['status'=>'pending','replacement_id'=>$replacementId],JSON_THROW_ON_ERROR)]);
        if ($this->automatic) (new AutomaticRewardService($this->pdo))->grant($id,$adminId,$policy);
    }

    public function summary(int $userId): array
    {
        $q = $this->pdo->prepare("SELECT COUNT(*) FROM reward_ledger WHERE user_id=? AND status='pending'");
        $q->execute([$userId]);
        $pending=(int)$q->fetchColumn();
        $policy=(new RewardPolicyService($this->pdo))->read();
        $q=$this->pdo->prepare("SELECT COUNT(*) AS credits,COALESCE(SUM(l.discount_percent),0) AS total
            FROM reward_ledger l JOIN track_replacements r ON r.id=l.replacement_id
            JOIN users u ON u.id=l.user_id JOIN user_email_security e ON e.user_id=u.id
            WHERE l.user_id=? AND l.grant_mode='manual' AND l.status='approved' AND l.expires_at>UTC_TIMESTAMP(6)
                AND u.status='active' AND e.verified_at IS NOT NULL
                AND r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL
                AND r.uploaded_by_user_id=l.user_id AND r.audio_asset_id=l.audio_asset_id");
        $q->execute([$userId]);$credits=$q->fetch(PDO::FETCH_ASSOC);
        $q=$this->pdo->prepare("SELECT a.available_from,a.discount_percent,a.validity_days,l.discount_percent AS earned
            FROM reward_allocations a JOIN reward_ledger l ON l.id=a.reward_id
            JOIN users u ON u.id=l.user_id WHERE l.user_id=? AND l.status='approved'
            AND u.status='active' AND a.redeemed_at IS NULL ORDER BY a.available_from,a.id");
        $q->execute([$userId]);$allocations=$q->fetchAll(PDO::FETCH_ASSOC);
        $today=$this->pdo->query('SELECT DATE(DATE_ADD(UTC_TIMESTAMP(),INTERVAL 3 HOUR))')->fetchColumn();$ready=0;$future=0;$next=null;
        $schedule=[];
        foreach($allocations as $a) {
            $amount=(int)$a['discount_percent'];$month=substr($a['available_from'],0,7);
            $schedule[$month]=($schedule[$month]??0)+$amount;
            if($a['available_from']<=$today) $ready+=$amount;
            else {$future+=$amount;$next??=$a['available_from'];}
        }
        $available=min($policy['max_discount_percent'],$ready);
        $queued=$future+max(0,$ready-$available);
        if ($queued>0 && $ready>$available) $next=(new \DateTimeImmutable(substr($today,0,7).'-01'))->modify('+1 month')->format('Y-m-d');
        $q=$this->pdo->prepare("SELECT COUNT(*),COALESCE(SUM(discount_percent),0) FROM reward_ledger WHERE user_id=? AND grant_mode='automatic' AND status='approved'");
        $q->execute([$userId]);$earned=$q->fetch(PDO::FETCH_NUM);
        return ['earned_contributions'=>(int)$earned[0], 'earned_discount_percent'=>(int)$earned[1],
            'available_discount_percent'=>$available,'carried_discount_percent'=>$queued,'next_available_from'=>$next,
            'waiting_for_payment'=>true,'expiry_starts'=>'payment','monthly_cap_percent'=>$policy['max_discount_percent'],
            'schedule'=>array_map(static fn($month,$percent)=>['month'=>$month,'percent'=>$percent],array_keys($schedule),array_values($schedule)),
            'pending_contributions' =>$pending, 'approved_credits'=>(int)$credits['credits'],
            'potential_discount_percent'=>min($policy['max_discount_percent'],(int)$credits['total']+$available),
            'reward_available'=>false,'discount_active'=>false,'application_available'=>false,
            'policy_configured'=>$policy['upload_discount_percent']>0 && $policy['max_reward_per_month']>0 && $policy['validity_days']>0,
            'issuance_enabled'=>(bool)$policy['enabled']];
    }
}
