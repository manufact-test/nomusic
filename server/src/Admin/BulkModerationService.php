<?php

declare(strict_types=1);

namespace Celikom\Admin;

use Celikom\Storage\StorageAdapter;

/**
 * Explicit, bounded operator-only bulk decisions. Each candidate is a separate
 * transaction: one stale row never silently changes or rolls back the other 49.
 */
final class BulkModerationService
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly StorageAdapter $storage,
        private readonly ?\Celikom\Reward\RewardService $rewards = null
    ) {}

    /** @return array<int,array{version:int,active:int}> */
    public static function selected(mixed $input): array
    {
        if (!is_array($input) || count($input) < 1 || count($input) > 50) {
            throw new \InvalidArgumentException('bulk_selection_count');
        }
        $selected = [];
        foreach ($input as $id => $state) {
            if (!preg_match('/^[1-9]\d{0,17}$/D', (string)$id)
                || !is_string($state)
                || !preg_match('/^([1-9]\d{0,9}):([0-9]\d{0,17})$/D', $state, $m)
                || (int)$m[1] > 4294967295
                || (string)(int)$id !== (string)$id) {
                throw new \InvalidArgumentException('bulk_selection_invalid');
            }
            $selected[(int)$id] = ['version'=>(int)$m[1], 'active'=>(int)$m[2]];
        }
        if (count($selected) !== count($input)) throw new \InvalidArgumentException('bulk_selection_duplicate');
        return $selected;
    }

    /** @return list<array<string,mixed>> */
    public function preview(array $selected, string $action, string $role): array
    {
        $this->authorize($action, $role);
        if (count($selected) < 1 || count($selected) > 50) throw new \InvalidArgumentException('bulk_selection_count');
        $ids = array_keys($selected);
        $sql = 'SELECT r.id,r.track_id,r.status,r.version,r.is_active,
                t.service,t.service_track_id,t.artist,t.title,
                (SELECT q.id FROM track_replacements q WHERE q.track_id=r.track_id
                 AND q.status=\'approved\' AND q.is_active=1 AND q.disabled_at IS NULL LIMIT 1) AS active_id
            FROM track_replacements r JOIN tracks t ON t.id=r.track_id WHERE r.id IN ('
            . implode(',', array_fill(0, count($ids), '?')) . ') ORDER BY r.id';
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($ids);
        $rows = $stmt->fetchAll(\PDO::FETCH_ASSOC);
        if (count($rows) !== count($selected)) throw new \DomainException('bulk_missing_candidate');
        foreach ($rows as $row) {
            $id = (int)$row['id'];
            if ((int)$row['version'] !== $selected[$id]['version']
                || (int)($row['active_id'] ?? 0) !== $selected[$id]['active']
                || (int)$row['is_active'] !== 0
                || !in_array($row['status'], $action === 'delete' ? ['pending','rejected'] : ['pending'], true)) {
                throw new \DomainException('bulk_stale_candidate_' . $id);
            }
        }
        return $rows;
    }

    /**
     * The frontend is never trusted: versions, active mapping, status and
     * rights confirmation are checked again in locked backend transactions.
     * @return array{batch:string,success:list<int>,conflicts:array<int,string>,cleanup_warnings:list<int>}
     */
    public function execute(
        int $adminId, string $role, array $selected, string $action,
        string $reason, bool $rightsConfirmed, bool $explicitConfirmation
    ): array {
        $this->authorize($action, $role);
        if ($adminId < 1 || count($selected) < 1 || count($selected) > 50
            || !$explicitConfirmation || trim($reason) === '' || strlen($reason) > 500) {
            throw new \InvalidArgumentException('bulk_confirmation_required');
        }
        if ($action === 'approve' && !$rightsConfirmed) {
            throw new \DomainException('approval_requires_rights_and_reason');
        }
        $batch = bin2hex(random_bytes(12));
        $result = ['batch'=>$batch,'success'=>[], 'conflicts'=>[], 'cleanup_warnings'=>[]];
        $mod = new ModerationService($this->pdo, $this->storage, $this->rewards);
        foreach ($selected as $id => $state) {
            try {
                if ($action === 'delete') {
                    $cleaned = $this->deleteCandidate($adminId, $id, $state, $reason, $batch);
                    if (!$cleaned) $result['cleanup_warnings'][] = $id;
                } else {
                    $mod->replacement($adminId, $id, $action, $reason, $state['active'],
                        $rightsConfirmed, $state['version'], $batch);
                }
                $result['success'][] = $id;
            } catch (\DomainException|\PDOException|\RuntimeException $e) {
                // Do not lose 49 successful operations if one record changed.
                $result['conflicts'][$id] = $e instanceof \DomainException ? $e->getMessage() : 'reference_or_storage_conflict';
            }
        }
        return $result;
    }

    private function authorize(string $action, string $role): void
    {
        if (!in_array($action, ['approve','reject','duplicate','wrong_track','bad_quality','delete'], true)
            || !in_array($role, ['owner','moderator'], true)
            || ($action === 'delete' && $role !== 'owner')) {
            throw new \InvalidArgumentException('bulk_action_not_allowed');
        }
    }

    private function deleteCandidate(int $adminId, int $id, array $expected, string $reason, string $batch): bool
    {
        $this->pdo->beginTransaction();
        $key = null;
        $assetId = null;
        try {
            // Match the existing track -> replacement lock order.
            $find = $this->pdo->prepare('SELECT track_id FROM track_replacements WHERE id=?');
            $find->execute([$id]);
            $trackId = $find->fetchColumn();
            if ($trackId === false) throw new \DomainException('candidate_missing');
            $lock = $this->pdo->prepare('SELECT id,service,service_track_id FROM tracks WHERE id=? FOR UPDATE');
            $lock->execute([(int)$trackId]);
            $track = $lock->fetch(\PDO::FETCH_ASSOC);
            if (!$track) throw new \DomainException('track_missing');
            $get = $this->pdo->prepare('SELECT * FROM track_replacements WHERE id=? FOR UPDATE');
            $get->execute([$id]);
            $row = $get->fetch(\PDO::FETCH_ASSOC);
            if (!$row || (int)$row['track_id'] !== (int)$trackId
                || (int)$row['version'] !== $expected['version']
                || (int)$row['is_active'] !== 0
                || !in_array($row['status'], ['pending','rejected'], true)) {
                throw new \DomainException('candidate_changed');
            }
            $active = $this->pdo->prepare("SELECT id FROM track_replacements WHERE track_id=?
                AND status='approved' AND is_active=1 AND disabled_at IS NULL FOR UPDATE");
            $active->execute([(int)$trackId]);
            if ((int)($active->fetchColumn() ?: 0) !== $expected['active']) {
                throw new \DomainException('stale_moderation_form');
            }
            // Fail closed for every current and future FK referencing this row:
            // an uploaded submission, complaint or reward is not destroyed.
            if ($this->hasForeignReferences('track_replacements', $id)) {
                throw new \DomainException('candidate_has_history_reject_instead');
            }
            $assetId = (int)$row['audio_asset_id'];
            $assetLock = $this->pdo->prepare('SELECT * FROM audio_assets WHERE id=? FOR UPDATE');
            $assetLock->execute([$assetId]);
            $asset = $assetLock->fetch(\PDO::FETCH_ASSOC);
            if (!$asset) throw new \DomainException('asset_missing');
            $refs = $this->pdo->prepare('SELECT id FROM track_replacements WHERE audio_asset_id=? ORDER BY id FOR UPDATE');
            $refs->execute([$assetId]);
            $shared = count($refs->fetchAll(\PDO::FETCH_COLUMN)) > 1;
            if (!$shared && $this->hasForeignReferences('audio_assets', $assetId, ['track_replacements','audio_fingerprint_jobs'])) {
                throw new \DomainException('asset_has_other_references');
            }
            $key = $shared ? null : (string)$asset['storage_key'];
            $this->pdo->prepare('DELETE FROM track_replacements WHERE id=?')->execute([$id]);
            if (!$shared) {
                $this->pdo->prepare('DELETE FROM audio_fingerprint_jobs WHERE audio_asset_id=?')->execute([$assetId]);
                $this->pdo->prepare('DELETE FROM audio_assets WHERE id=?')->execute([$assetId]);
            }
            $this->pdo->prepare('INSERT INTO bulk_moderation_tombstones
                (batch_id,replacement_id,service,service_track_id,sha256,asset_id,storage_key,cleanup_status)
                VALUES (?,?,?,?,?,?,?,?)')->execute([
                    $batch,$id,$track['service'],$track['service_track_id'],$asset['sha256'],
                    $assetId,$key,$shared ? 'shared' : 'pending'
                ]);
            (new ModerationService($this->pdo, $this->storage))->audit(
                $adminId,'replacement_bulk_delete','track_replacement',$id,$reason,
                ['track_id'=>$track['service_track_id'],'status'=>$row['status'],'version'=>(int)$row['version']],
                ['deleted'=>true,'batch_id'=>$batch,'shared_asset'=>$shared]
            );
            $this->pdo->commit();
        } catch (\Throwable $e) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $e;
        }
        if ($key === null) return true;
        // No public route is allowed to stream the deleted row. Recheck key reuse
        // before cleanup; failed cleanup remains recorded for safe manual retry.
        try {
            $test = $this->pdo->prepare('SELECT id FROM audio_assets WHERE storage_key=? LIMIT 1');
            $test->execute([$key]);
            if ($test->fetchColumn() !== false) return false;
            $this->storage->delete($key);
            $this->pdo->prepare("UPDATE bulk_moderation_tombstones SET cleanup_status='done'
                WHERE replacement_id=? AND cleanup_status='pending'")->execute([$id]);
            return true;
        } catch (\Throwable $e) {
            $this->pdo->prepare("UPDATE bulk_moderation_tombstones SET cleanup_status='failed'
                WHERE replacement_id=? AND cleanup_status='pending'")->execute([$id]);
            return false;
        }
    }

    private function hasForeignReferences(string $table, int $id, array $ignore = []): bool
    {
        $refs = $this->pdo->prepare('SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA=DATABASE() AND REFERENCED_TABLE_SCHEMA=DATABASE()
            AND REFERENCED_TABLE_NAME=? AND REFERENCED_COLUMN_NAME=\'id\'');
        $refs->execute([$table]);
        foreach ($refs->fetchAll(\PDO::FETCH_ASSOC) as $ref) {
            $child = (string)$ref['TABLE_NAME'];
            $column = (string)$ref['COLUMN_NAME'];
            if (in_array($child, $ignore, true)) continue;
            if (!preg_match('/^[a-zA-Z_][a-zA-Z_0-9]*$/D', $child)
                || !preg_match('/^[a-zA-Z_][a-zA-Z_0-9]*$/D', $column)) {
                throw new \DomainException('invalid_foreign_reference');
            }
            $q = $this->pdo->prepare("SELECT 1 FROM `$child` WHERE `$column`=? LIMIT 1");
            $q->execute([$id]);
            if ($q->fetchColumn() !== false) return true;
        }
        return false;
    }
}
