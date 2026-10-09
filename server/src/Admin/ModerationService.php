<?php

declare(strict_types=1);

namespace Celikom\Admin;

use Celikom\Storage\StorageAdapter;

/**
 * Stage 8.3–8.4. Every decision, mapping change and audit entry commits together.
 * Never invoked from an upload request; there is no auto-approval path.
 */
final class ModerationService
{
    public function __construct(private readonly \PDO $pdo, private readonly StorageAdapter $storage) {}

    public function replacement(int $adminId, int $id, string $action, string $reason, int $expectedActive, bool $rightsConfirmed): void
    {
        if ($adminId < 1 || $id < 1 || $expectedActive < 0
            || !in_array($action, ['approve','reject','duplicate','wrong_track','bad_quality','disable'], true)
            || mb_strlen($reason) > 500 || ($action !== 'approve' && trim($reason) === '')) {
            throw new \InvalidArgumentException('invalid_moderation_action');
        }
        if ($action === 'approve' && (!$rightsConfirmed || trim($reason) === '')) {
            throw new \DomainException('approval_requires_rights_and_reason');
        }
        $this->pdo->beginTransaction();
        try {
            // The same lock order as LibraryManagementService prevents approval races.
            $find = $this->pdo->prepare('SELECT track_id FROM track_replacements WHERE id = ?');
            $find->execute([$id]);
            $trackId = $find->fetchColumn();
            if ($trackId === false) throw new \DomainException('candidate_missing');
            $lock = $this->pdo->prepare('SELECT id FROM tracks WHERE id = ? FOR UPDATE');
            $lock->execute([(int) $trackId]);
            if (!$lock->fetchColumn()) throw new \DomainException('track_missing');
            $get = $this->pdo->prepare('SELECT * FROM track_replacements WHERE id = ? FOR UPDATE');
            $get->execute([$id]);
            $before = $get->fetch(\PDO::FETCH_ASSOC);
            if (!$before || (int) $before['track_id'] !== (int) $trackId) throw new \DomainException('candidate_changed');
            $active = $this->pdo->prepare("SELECT id FROM track_replacements WHERE track_id = ?
                AND status = 'approved' AND is_active = 1 AND disabled_at IS NULL FOR UPDATE");
            $active->execute([(int) $trackId]);
            $current = $active->fetchColumn();
            if ((int) ($current === false ? 0 : $current) !== $expectedActive) {
                throw new \DomainException('stale_moderation_form');
            }
            if ($action === 'approve') {
                if ($before['status'] !== 'pending' || (int) $before['is_active'] !== 0) {
                    throw new \DomainException('candidate_not_pending');
                }
                $asset = $this->pdo->prepare('SELECT storage_driver,storage_key,size_bytes,mime_type FROM audio_assets WHERE id=?');
                $asset->execute([(int) $before['audio_asset_id']]);
                $a = $asset->fetch(\PDO::FETCH_ASSOC);
                if (!$a || $a['storage_driver'] !== 'local' ||
                    !in_array($a['mime_type'], ['audio/mpeg','audio/wav','audio/x-wav'], true) ||
                    !$this->storage->exists($a['storage_key']) ||
                    $this->storage->getSize($a['storage_key']) !== (int) $a['size_bytes']) {
                    throw new \DomainException('candidate_audio_unavailable');
                }
                $this->pdo->prepare('UPDATE track_replacements SET is_active=0 WHERE track_id=? AND is_active=1')
                    ->execute([(int) $trackId]);
                $this->pdo->prepare("UPDATE track_replacements SET status='approved',is_active=1,
                    version=version+1,approved_by_admin_id=?,approved_at=UTC_TIMESTAMP(6),disabled_at=NULL WHERE id=?")
                    ->execute([$adminId,$id]);
            } elseif ($action === 'disable') {
                if ($before['status'] !== 'approved' || (int) $before['is_active'] !== 1) {
                    throw new \DomainException('candidate_not_active');
                }
                $this->pdo->prepare("UPDATE track_replacements SET status='disabled',is_active=0,
                    disabled_at=UTC_TIMESTAMP(6),version=version+1 WHERE id=?")
                    ->execute([$id]);
            } else {
                if ($before['status'] !== 'pending' || (int) $before['is_active'] !== 0) {
                    throw new \DomainException('candidate_not_pending');
                }
                $this->pdo->prepare("UPDATE track_replacements SET status='rejected',is_active=0,
                    version=version+1 WHERE id=?")->execute([$id]);
            }
            $after = $get;
            $after->execute([$id]);
            $result = $after->fetch(\PDO::FETCH_ASSOC);
            $this->audit($adminId, 'replacement_' . $action, 'track_replacement', $id, $reason,
                self::snapshot($before), self::snapshot($result));
            $this->pdo->commit();
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }

    public function trackRequest(int $adminId, int $id, string $action, string $reason): void
    {
        if ($adminId < 1 || $id < 1 || !in_array($action, ['reviewed','rejected'], true)
            || mb_strlen($reason) > 500 || trim($reason) === '') {
            throw new \InvalidArgumentException('invalid_request_review');
        }
        $this->pdo->beginTransaction();
        try {
            $find = $this->pdo->prepare('SELECT id,status FROM track_requests WHERE id=? FOR UPDATE');
            $find->execute([$id]);
            $before = $find->fetch(\PDO::FETCH_ASSOC);
            if (!$before || $before['status'] !== 'pending') throw new \DomainException('request_not_pending');
            $this->pdo->prepare('UPDATE track_requests SET status=? WHERE id=?')->execute([$action,$id]);
            $this->pdo->prepare('INSERT INTO track_request_reviews (track_request_id,admin_id,reason)
                VALUES (?,?,?)')->execute([$id,$adminId,$reason]);
            $this->audit($adminId,'track_request_' . $action,'track_request',$id,$reason,
                ['status'=>'pending'],['status'=>$action]);
            $this->pdo->commit();
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }

    public function audit(int $adminId, string $action, string $type, int $id, string $reason, array $before, array $after): void
    {
        $this->pdo->prepare('INSERT INTO audit_log
            (admin_id,action,entity_type,entity_id,reason,before_json,after_json) VALUES (?,?,?,?,?,?,?)')
            ->execute([$adminId,$action,$type,$id,$reason,
                json_encode($before, JSON_THROW_ON_ERROR),json_encode($after, JSON_THROW_ON_ERROR)]);
    }

    private static function snapshot(array $row): array
    {
        return ['status'=>$row['status'],'is_active'=>(int)$row['is_active'],
            'version'=>(int)$row['version'],'approved_by_admin_id'=>$row['approved_by_admin_id']];
    }
}
