<?php

declare(strict_types=1);

namespace Celikom\Application;

use Celikom\Storage\StorageAdapter;

/**
 * Owner-only, internal Stage 6 library operations. This class is intentionally
 * not routed from HTTP. User uploads and admin moderation belong to Stages 7–8.
 */
final class LibraryManagementService
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly StorageAdapter $storage,
        private readonly int $maxBytes = 31457280,
    ) {
    }

    public function addTrack(string $service, string $trackId, int $durationMs, array $metadata = []): int
    {
        if ($service !== 'yandex' || !preg_match('/^[1-9]\d{0,23}$/D', $trackId)
            || $durationMs < 1000 || $durationMs > 86400000) {
            throw new \InvalidArgumentException('invalid_library_track');
        }
        $query = $this->pdo->prepare('INSERT INTO tracks (service, service_track_id, artist, title, album, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)');
        $query->execute([$service, $trackId, substr((string) ($metadata['artist'] ?? ''), 0, 240),
            substr((string) ($metadata['title'] ?? ''), 0, 240),
            substr((string) ($metadata['album'] ?? ''), 0, 240), $durationMs]);
        return (int) $this->pdo->lastInsertId();
    }

    /**
     * Registers only an explicitly owner-reviewed local audio fixture.
     * The caller (future restricted CLI) must separately enforce the staging path.
     */
    public function addReviewedAsset(string $file, int $durationMs, bool $ownerReviewed): int
    {
        if (!$ownerReviewed) {
            throw new \InvalidArgumentException('owner_review_required');
        }
        if ($durationMs < 1000 || $durationMs > 86400000 || !is_file($file) || is_link($file)) {
            throw new \InvalidArgumentException('invalid_library_asset');
        }
        $size = filesize($file);
        $mime = (new \finfo(FILEINFO_MIME_TYPE))->file($file);
        $extensions = ['audio/mpeg' => 'mp3', 'audio/wav' => 'wav', 'audio/x-wav' => 'wav'];
        if ($size === false || $size < 1 || $size > $this->maxBytes || !isset($extensions[$mime])) {
            throw new \InvalidArgumentException('unsupported_library_asset');
        }
        $hash = hash_file('sha256', $file);
        if ($hash === false) {
            throw new \RuntimeException('library_asset_unreadable');
        }
        $key = 'audio/' . substr($hash, 0, 2) . '/' . $hash . '.' . $extensions[$mime];
        if (!$this->storage->exists($key)) {
            $stream = fopen($file, 'rb');
            if ($stream === false) {
                throw new \RuntimeException('library_asset_unreadable');
            }
            try {
                $this->storage->put($key, $stream);
            } finally {
                fclose($stream);
            }
        }
        if ($this->storage->getSize($key) !== $size) {
            throw new \RuntimeException('library_asset_size_mismatch');
        }
        $query = $this->pdo->prepare('INSERT INTO audio_assets
            (storage_driver, storage_key, sha256, mime_type, size_bytes, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)');
        $query->execute(['local', $key, $hash, $mime, $size, $durationMs]);
        $assetId = (int) $this->pdo->lastInsertId();
        $asset = $this->asset($assetId);
        if ($asset['sha256'] !== $hash || $asset['storage_driver'] !== 'local'
            || $asset['storage_key'] !== $key || $asset['mime_type'] !== $mime
            || (int) $asset['size_bytes'] !== $size || (int) $asset['duration_ms'] !== $durationMs) {
            throw new \RuntimeException('library_asset_metadata_conflict');
        }
        return $assetId;
    }

    /** Creates a pending, inactive candidate. Never publishes or approves it. */
    public function link(int $trackId, int $assetId): int
    {
        if ($trackId <= 0 || $assetId <= 0) {
            throw new \InvalidArgumentException('invalid_library_link');
        }
        $this->pdo->beginTransaction();
        try {
            $track = $this->pdo->prepare('SELECT id FROM tracks WHERE id = ? FOR UPDATE');
            $track->execute([$trackId]);
            if ($track->fetchColumn() === false) {
                throw new \InvalidArgumentException('library_track_missing');
            }
            $this->ensureAssetAvailable($this->asset($assetId));
            $prior = $this->pdo->prepare("SELECT id FROM track_replacements
                WHERE track_id = ? AND audio_asset_id = ?
                AND status IN ('pending', 'approved') AND disabled_at IS NULL
                ORDER BY id LIMIT 1");
            $prior->execute([$trackId, $assetId]);
            $existingId = $prior->fetchColumn();
            if ($existingId !== false) {
                $this->pdo->commit();
                return (int) $existingId;
            }
            $insert = $this->pdo->prepare("INSERT INTO track_replacements
                (track_id, audio_asset_id, status, is_active) VALUES (?, ?, 'pending', 0)");
            $insert->execute([$trackId, $assetId]);
            $newId = (int) $this->pdo->lastInsertId();
            $this->pdo->commit();
            return $newId;
        } catch (\Throwable $error) {
            $this->pdo->rollBack();
            throw $error;
        }
    }

    /** Explicit, owner-only approval is separate from activation. */
    public function approve(int $replacementId, bool $ownerReviewed): void
    {
        if (!$ownerReviewed) {
            throw new \InvalidArgumentException('owner_review_required');
        }
        $this->withLockedReplacement($replacementId, function (array $row): void {
            if ($row['status'] === 'approved' && $row['disabled_at'] === null) {
                return;
            }
            if ($row['status'] !== 'pending') {
                throw new \InvalidArgumentException('library_candidate_not_pending');
            }
            $this->ensureAssetAvailable($this->asset((int) $row['audio_asset_id']));
            $query = $this->pdo->prepare("UPDATE track_replacements SET status = 'approved', is_active = 0,
                approved_at = CURRENT_TIMESTAMP(6) WHERE id = ?");
            $query->execute([(int) $row['id']]);
        });
    }

    /** Serializes per Track. Increasing version revokes any older signed link on reactivation. */
    public function activate(int $replacementId, bool $ownerConfirmed): void
    {
        if (!$ownerConfirmed) {
            throw new \InvalidArgumentException('owner_activation_required');
        }
        $this->withLockedReplacement($replacementId, function (array $row): void {
            if ($row['status'] !== 'approved' || $row['disabled_at'] !== null || $row['approved_at'] === null) {
                throw new \InvalidArgumentException('library_candidate_not_approved');
            }
            $this->ensureAssetAvailable($this->asset((int) $row['audio_asset_id']));
            if ((int) $row['is_active'] === 1) {
                return;
            }
            if ((int) $row['version'] >= 4294967295) {
                throw new \RuntimeException('library_version_exhausted');
            }
            $this->pdo->prepare('UPDATE track_replacements SET is_active = 0 WHERE track_id = ? AND is_active = 1')
                ->execute([(int) $row['track_id']]);
            $this->pdo->prepare('UPDATE track_replacements SET is_active = 1, version = version + 1 WHERE id = ?')
                ->execute([(int) $row['id']]);
        });
    }

    public function disable(int $replacementId, bool $ownerConfirmed): void
    {
        if (!$ownerConfirmed) {
            throw new \InvalidArgumentException('owner_activation_required');
        }
        $this->withLockedReplacement($replacementId, function (array $row): void {
            if ($row['status'] === 'disabled') {
                return;
            }
            if ((int) $row['version'] >= 4294967295) {
                throw new \RuntimeException('library_version_exhausted');
            }
            $this->pdo->prepare("UPDATE track_replacements SET is_active = 0, status = 'disabled',
                disabled_at = CURRENT_TIMESTAMP(6), version = version + 1 WHERE id = ?")
                ->execute([(int) $row['id']]);
        });
    }

    private function asset(int $id): array
    {
        $query = $this->pdo->prepare('SELECT * FROM audio_assets WHERE id = ?');
        $query->execute([$id]);
        return $query->fetch(\PDO::FETCH_ASSOC) ?: throw new \InvalidArgumentException('library_asset_missing');
    }

    private function ensureAssetAvailable(array $asset): void
    {
        if ($asset['storage_driver'] !== 'local' ||
            !in_array($asset['mime_type'], ['audio/mpeg', 'audio/wav', 'audio/x-wav'], true) ||
            !$this->storage->exists($asset['storage_key']) ||
            $this->storage->getSize($asset['storage_key']) !== (int) $asset['size_bytes']) {
            throw new \RuntimeException('library_asset_unavailable');
        }
    }

    private function withLockedReplacement(int $id, callable $operation): void
    {
        if ($id <= 0) {
            throw new \InvalidArgumentException('invalid_library_replacement');
        }
        $this->pdo->beginTransaction();
        try {
            $find = $this->pdo->prepare('SELECT track_id FROM track_replacements WHERE id = ?');
            $find->execute([$id]);
            $trackId = $find->fetchColumn();
            if ($trackId === false) {
                throw new \InvalidArgumentException('library_replacement_missing');
            }
            $lock = $this->pdo->prepare('SELECT id FROM tracks WHERE id = ? FOR UPDATE');
            $lock->execute([(int) $trackId]);
            if ($lock->fetchColumn() === false) {
                throw new \RuntimeException('library_track_missing');
            }
            $candidate = $this->pdo->prepare('SELECT * FROM track_replacements WHERE id = ? FOR UPDATE');
            $candidate->execute([$id]);
            $row = $candidate->fetch(\PDO::FETCH_ASSOC);
            if (!$row || (int) $row['track_id'] !== (int) $trackId) {
                throw new \RuntimeException('library_candidate_changed');
            }
            $operation($row);
            $this->pdo->commit();
        } catch (\Throwable $error) {
            $this->pdo->rollBack();
            throw $error;
        }
    }
}
