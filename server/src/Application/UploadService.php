<?php

declare(strict_types=1);

namespace Celikom\Application;

use Celikom\Storage\StorageAdapter;

/**
 * Private owner-only staging. No approval code or public playback exposure.
 * The HTTP layer must authenticate a dedicated owner upload credential first.
 */
final class UploadService
{
    private readonly \Closure $uploadVerifier;

    public function __construct(
        private readonly \PDO $pdo,
        private readonly StorageAdapter $storage,
        private readonly int $maxBytes = 31457280,
        ?\Closure $uploadVerifier = null,
        private readonly ?AudioFingerprintService $fingerprints = null,
    ) {
        $this->uploadVerifier = $uploadVerifier ?? static fn (string $path): bool => is_uploaded_file($path);
    }

    /** @param array<string, mixed> $fields @param array<string, mixed> $file */
    public function upload(array $fields, array $file, string $uploaderHash): array
    {
        if (!preg_match('/^[a-f0-9]{64}$/D', $uploaderHash)) {
            throw new \InvalidArgumentException('invalid_uploader');
        }
        if (($fields['declaration'] ?? null) !== '1') {
            throw new \DomainException('rights_declaration_required');
        }
        $service = $fields['service'] ?? null;
        $trackId = $fields['track_id'] ?? null;
        $duration = $fields['duration_ms'] ?? null;
        $requestId = $fields['request_id'] ?? null;
        if ($service !== 'yandex' || !is_string($trackId) || !preg_match('/^[1-9]\d{0,23}$/D', $trackId)
            || !is_string($duration) || !preg_match('/^[1-9]\d{0,7}$/D', $duration)
            || (int) $duration < 1000 || (int) $duration > 86400000
            || !is_string($requestId) || !preg_match('/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/iD', $requestId)) {
            throw new \InvalidArgumentException('invalid_upload_metadata');
        }
        $metadata = [];
        foreach (['artist', 'title', 'album'] as $key) {
            $value = $fields[$key] ?? '';
            if (!is_string($value) || strlen($value) > 240 || !preg_match('//u', $value)
                || preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F]/', $value)) {
                throw new \InvalidArgumentException('invalid_upload_metadata');
            }
            $metadata[$key] = trim($value);
        }
        if (($file['error'] ?? null) === UPLOAD_ERR_INI_SIZE || ($file['error'] ?? null) === UPLOAD_ERR_FORM_SIZE) {
            throw new \LengthException('upload_too_large');
        }
        if (($file['error'] ?? null) !== UPLOAD_ERR_OK || !is_string($file['tmp_name'] ?? null)
            || !is_string($file['name'] ?? null) || !is_int($file['size'] ?? null)) {
            throw new \InvalidArgumentException('invalid_upload_file');
        }
        $path = $file['tmp_name'];
        if (!(($this->uploadVerifier)($path)) || is_link($path) || !is_file($path)) {
            throw new \InvalidArgumentException('invalid_upload_file');
        }
        $size = @filesize($path);
        if ($size === false || $size < 1024 || $size !== $file['size']) {
            throw new \InvalidArgumentException('invalid_upload_file');
        }
        if ($size > $this->maxBytes) {
            throw new \LengthException('upload_too_large');
        }
        // A .mp3 suffix and browser supplied MIME are never sufficient.
        if ((new \finfo(FILEINFO_MIME_TYPE))->file($path) !== 'audio/mpeg'
            || !(new Mp3Inspector())->check($path)) {
            throw new \DomainException('invalid_mp3');
        }
        $sha = hash_file('sha256', $path);
        if ($sha === false) throw new \RuntimeException('upload_hash_failed');

        $existing = $this->submission($uploaderHash, $requestId);
        if ($existing !== null) {
            if ($existing['service'] !== $service || $existing['service_track_id'] !== $trackId || $existing['sha256'] !== $sha) {
                throw new \DomainException('idempotency_conflict');
            }
            return ['status' => 'pending', 'replacement_id' => (int) $existing['replacement_id'], 'duplicate' => true];
        }

        // Avoid writing a second physical file for any already registered digest.
        $lookup = $this->pdo->prepare('SELECT * FROM audio_assets WHERE sha256 = ?');
        $lookup->execute([$sha]);
        $knownAsset = $lookup->fetch(\PDO::FETCH_ASSOC) ?: null;
        $key = $knownAsset['storage_key'] ?? ('audio/' . substr($sha, 0, 2) . '/' . $sha . '.mp3');
        if ($knownAsset !== null && ($knownAsset['storage_driver'] !== 'local' || $knownAsset['mime_type'] !== 'audio/mpeg'
            || (int) $knownAsset['size_bytes'] !== $size)) {
            throw new \DomainException('asset_conflict');
        }
        if (!$this->storage->exists($key)) {
            $source = @fopen($path, 'rb');
            if ($source === false) throw new \RuntimeException('upload_unreadable');
            try {
                $this->storage->put($key, $source);
            } finally {
                fclose($source);
            }
        }
        if ($this->storage->getSize($key) !== $size) throw new \RuntimeException('upload_storage_mismatch');

        // The Track row is the cross-request serialization point, preserving
        // one pending candidate for the same Track + digest under concurrency.
        $this->pdo->beginTransaction();
        try {
            $track = (new LibraryManagementService($this->pdo, $this->storage))
                ->addTrack($service, $trackId, (int) $duration, $metadata);
            $stmt = $this->pdo->prepare('SELECT id FROM tracks WHERE id = ? FOR UPDATE');
            $stmt->execute([$track]);
            if ($stmt->fetchColumn() === false) throw new \RuntimeException('track_missing');
            $stmt = $this->pdo->prepare('INSERT INTO audio_assets
                (storage_driver, storage_key, sha256, mime_type, size_bytes, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)');
            $stmt->execute(['local', $key, $sha, 'audio/mpeg', $size, (int) $duration]);
            $assetId = (int) $this->pdo->lastInsertId();
            $stmt = $this->pdo->prepare('SELECT * FROM audio_assets WHERE id = ?');
            $stmt->execute([$assetId]);
            $asset = $stmt->fetch(\PDO::FETCH_ASSOC);
            if (!$asset || $asset['sha256'] !== $sha || $asset['storage_key'] !== $key
                || $asset['storage_driver'] !== 'local' || $asset['mime_type'] !== 'audio/mpeg'
                || (int) $asset['size_bytes'] !== $size) throw new \DomainException('asset_conflict');

            $stmt = $this->pdo->prepare("SELECT id, status FROM track_replacements
                WHERE track_id = ? AND audio_asset_id = ? AND status IN ('pending', 'approved')
                  AND disabled_at IS NULL ORDER BY id LIMIT 1");
            $stmt->execute([$track, $assetId]);
            $prior = $stmt->fetch(\PDO::FETCH_ASSOC);
            if ($prior && $prior['status'] === 'approved') {
                throw new \DomainException('already_approved');
            }
            $duplicate = (bool) $prior;
            if ($prior) {
                $replacementId = (int) $prior['id'];
            } else {
                $stmt = $this->pdo->prepare("INSERT INTO track_replacements
                    (track_id, audio_asset_id, status, is_active) VALUES (?, ?, 'pending', 0)");
                $stmt->execute([$track, $assetId]);
                $replacementId = (int) $this->pdo->lastInsertId();
            }
            $this->fingerprints?->schedule($assetId);
            $stmt = $this->pdo->prepare('INSERT INTO upload_submissions
                (uploader_hash, request_id, service, service_track_id, sha256, replacement_id)
                VALUES (?, ?, ?, ?, ?, ?)');
            $stmt->execute([$uploaderHash, strtolower($requestId), $service, $trackId, $sha, $replacementId]);
            $this->pdo->commit();
            return ['status' => 'pending', 'replacement_id' => $replacementId, 'duplicate' => $duplicate];
        } catch (\Throwable $error) {
            $this->pdo->rollBack();
            if ($error instanceof \PDOException && ($error->errorInfo[1] ?? null) === 1062) {
                $retry = $this->submission($uploaderHash, $requestId);
                if ($retry && $retry['sha256'] === $sha && $retry['service_track_id'] === $trackId && $retry['service'] === $service) {
                    return ['status' => 'pending', 'replacement_id' => (int) $retry['replacement_id'], 'duplicate' => true];
                }
                throw new \DomainException('idempotency_conflict');
            }
            throw $error;
        }
    }

    private function submission(string $owner, string $id): ?array
    {
        $stmt = $this->pdo->prepare('SELECT * FROM upload_submissions WHERE uploader_hash = ? AND request_id = ?');
        $stmt->execute([$owner, strtolower($id)]);
        return $stmt->fetch(\PDO::FETCH_ASSOC) ?: null;
    }
}
