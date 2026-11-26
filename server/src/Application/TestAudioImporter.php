<?php

declare(strict_types=1);

namespace Celikom\Application;

use Celikom\Storage\StorageAdapter;

/** Internal reviewed fixtures only. User uploads/moderation remain later stages. */
final class TestAudioImporter
{
    public function __construct(private readonly \PDO $pdo, private readonly StorageAdapter $storage, private readonly int $maxBytes = 31457280)
    {
    }

    public function import(string $file, string $service, string $trackId, int $durationMs, array $metadata = []): int
    {
        if ($service !== 'yandex' || !preg_match('/^[1-9]\d{0,23}$/D', $trackId) || $durationMs < 1000 || $durationMs > 86400000 || !is_file($file)) {
            throw new \InvalidArgumentException('invalid_test_audio');
        }
        $size = filesize($file);
        $mime = (new \finfo(FILEINFO_MIME_TYPE))->file($file);
        $extensions = ['audio/mpeg' => 'mp3', 'audio/wav' => 'wav', 'audio/x-wav' => 'wav'];
        if ($size === false || $size <= 0 || $size > $this->maxBytes || !isset($extensions[$mime])) {
            throw new \InvalidArgumentException('unsupported_test_audio');
        }
        $hash = hash_file('sha256', $file);
        if ($hash === false) {
            throw new \RuntimeException('test_audio_unreadable');
        }
        $key = 'audio/' . substr($hash, 0, 2) . '/' . $hash . '.' . $extensions[$mime];
        if (!$this->storage->exists($key)) {
            $source = fopen($file, 'rb');
            if ($source === false) {
                throw new \RuntimeException('test_audio_unreadable');
            }
            try {
                $this->storage->put($key, $source);
            } finally {
                fclose($source);
            }
        }
        $this->pdo->beginTransaction();
        try {
            $track = $this->pdo->prepare('INSERT INTO tracks (service, service_track_id, artist, title, album, duration_ms) VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6)');
            $track->execute([$service, $trackId, substr($metadata['artist'] ?? '', 0, 240), substr($metadata['title'] ?? '', 0, 240), substr($metadata['album'] ?? '', 0, 240), $durationMs]);
            $select = $this->pdo->prepare('SELECT id FROM tracks WHERE service = ? AND service_track_id = ? FOR UPDATE');
            $select->execute([$service, $trackId]);
            $internalId = (int) $select->fetchColumn();
            $asset = $this->pdo->prepare('INSERT INTO audio_assets (storage_driver, storage_key, sha256, mime_type, size_bytes, duration_ms) VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)');
            $asset->execute(['local', $key, $hash, $mime, $size, $durationMs]);
            $assetId = (int) $this->pdo->lastInsertId();
            $old = $this->pdo->prepare('SELECT id FROM track_replacements WHERE track_id = ? AND audio_asset_id = ? AND status = ? AND is_active = 1 AND disabled_at IS NULL');
            $old->execute([$internalId, $assetId, 'approved']);
            $existing = $old->fetchColumn();
            if ($existing !== false) {
                $this->pdo->commit();
                return (int) $existing;
            }
            $deactivate = $this->pdo->prepare('UPDATE track_replacements SET is_active = 0 WHERE track_id = ?');
            $deactivate->execute([$internalId]);
            $mapping = $this->pdo->prepare("INSERT INTO track_replacements (track_id, audio_asset_id, status, is_active, approved_at) VALUES (?, ?, 'approved', 1, CURRENT_TIMESTAMP(6))");
            $mapping->execute([$internalId, $assetId]);
            $id = (int) $this->pdo->lastInsertId();
            $this->pdo->commit();
            return $id;
        } catch (\Throwable $error) {
            $this->pdo->rollBack();
            throw $error;
        }
    }
}
