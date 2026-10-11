<?php

declare(strict_types=1);

namespace Celikom\Reward;

use PDO;

/** Evidence for a future configured reward, never an entitlement or a discount. */
final class RewardService
{
    public function __construct(private readonly PDO $pdo) {}

    /** Called only inside the transaction that approves a pending upload. */
    public function recordApprovedUpload(int $replacementId, int $adminId): void
    {
        if (!$this->pdo->inTransaction()) throw new \LogicException('reward_requires_moderation_transaction');
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
        $q = $this->pdo->prepare('SELECT id FROM reward_ledger WHERE audio_asset_id=?');
        $q->execute([$assetId]);
        if ($q->fetchColumn()) return;
        $this->pdo->prepare('INSERT INTO reward_ledger(user_id,audio_asset_id,replacement_id,approved_by_admin_id)
            VALUES(?,?,?,?)')->execute([(int)$row['uploaded_by_user_id'],(int)$assetId,$replacementId,$adminId]);
        $id = (int)$this->pdo->lastInsertId();
        $this->pdo->prepare('INSERT INTO audit_log(admin_id,action,entity_type,entity_id,reason,before_json,after_json)
            VALUES(?,?,?,?,?,?,?)')->execute([$adminId,'reward_eligibility_recorded','reward_ledger',$id,
                'approved_upload_pending_reward_policy','{}',json_encode(['status'=>'pending','replacement_id'=>$replacementId],JSON_THROW_ON_ERROR)]);
    }

    public function summary(int $userId): array
    {
        $q = $this->pdo->prepare("SELECT COUNT(*) FROM reward_ledger WHERE user_id=? AND status='pending'");
        $q->execute([$userId]);
        return ['pending_contributions'=>(int)$q->fetchColumn(), 'reward_available'=>false,
            'discount_active'=>false, 'policy_configured'=>false];
    }
}
