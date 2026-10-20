<?php
declare(strict_types=1);

namespace Celikom\Admin;

/** Owner-only catalogue label repair: does not change Track ID, media, or replacement state. */
final class MetadataService
{
    public function __construct(private readonly \PDO $pdo) {}

    public function update(int $adminId, int $trackDatabaseId, string $expectedServiceId,
        string $artist, string $title): void
    {
        $artist = trim($artist);
        $title = trim($title);
        if ($adminId < 1 || $trackDatabaseId < 1
            || !preg_match('/^[1-9]\d{0,23}$/D', $expectedServiceId)
            || $title === ''
            || mb_strlen($artist, 'UTF-8') > 240 || mb_strlen($title, 'UTF-8') > 240
            || preg_match('/[\x00-\x1F\x7F]/u', $artist . $title)) {
            throw new \InvalidArgumentException('invalid_track_metadata');
        }
        $this->pdo->beginTransaction();
        try {
            $q = $this->pdo->prepare('SELECT id,service,service_track_id,artist,title FROM tracks WHERE id=? FOR UPDATE');
            $q->execute([$trackDatabaseId]);
            $before = $q->fetch(\PDO::FETCH_ASSOC);
            if (!$before || $before['service'] !== 'yandex'
                || $before['service_track_id'] !== $expectedServiceId) {
                throw new \DomainException('stale_metadata');
            }
            // Previously complete metadata is intentionally immutable in this repair flow.
            if (trim((string) $before['artist']) !== '' && trim((string) $before['title']) !== '') {
                throw new \DomainException('already_labeled');
            }
            $this->pdo->prepare('UPDATE tracks SET artist=?,title=? WHERE id=?')
                ->execute([$artist, $title, $trackDatabaseId]);
            $this->pdo->prepare('INSERT INTO audit_log
                (admin_id,action,entity_type,entity_id,reason,before_json,after_json)
                VALUES (?,?,?,?,?,?,?)')
                ->execute([$adminId, 'track_metadata_labeled', 'track', $trackDatabaseId,
                    'Owner verified display metadata', json_encode([
                        'artist'=>$before['artist'],'title'=>$before['title']
                    ], JSON_THROW_ON_ERROR), json_encode([
                        'artist'=>$artist,'title'=>$title
                    ], JSON_THROW_ON_ERROR)]);
            $this->pdo->commit();
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }
}
