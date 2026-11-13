<?php

declare(strict_types=1);

namespace Celikom\Admin;

/**
 * Owner-only exact native Yandex identity attestation.
 * Values are opaque host identifiers; never infer them from title/artist/cover.
 */
final class NativeIdentityService
{
    public function __construct(private readonly \PDO $pdo) {}

    public function update(int $adminId, int $trackDatabaseId, string $expectedServiceId,
        ?string $albumId, ?string $editionId): bool
    {
        if ($adminId < 1 || $trackDatabaseId < 1
            || !preg_match('/^[1-9]\d{0,23}$/D', $expectedServiceId)
            || (($albumId === null) !== ($editionId === null))) {
            throw new \InvalidArgumentException('invalid_native_identity');
        }
        if ($albumId !== null && (
            !preg_match('/^[1-9]\d{0,23}$/D', $albumId)
            || $editionId === null
            || trim($editionId) === ''
            || mb_strlen($editionId, 'UTF-8') > 128
            || preg_match('/[\x00-\x1F\x7F]/u', $editionId)
        )) {
            throw new \InvalidArgumentException('invalid_native_identity');
        }

        $this->pdo->beginTransaction();
        try {
            $lock = $this->pdo->getAttribute(\PDO::ATTR_DRIVER_NAME) === 'mysql'
                ? ' FOR UPDATE' : '';
            $q = $this->pdo->prepare(
                'SELECT id,service,service_track_id,service_album_id,service_edition_id
                 FROM tracks WHERE id=?' . $lock
            );
            $q->execute([$trackDatabaseId]);
            $before = $q->fetch(\PDO::FETCH_ASSOC);
            if (!$before || $before['service'] !== 'yandex'
                || $before['service_track_id'] !== $expectedServiceId) {
                throw new \DomainException('stale_native_identity');
            }

            $oldAlbum = $before['service_album_id'] === null
                ? null : (string)$before['service_album_id'];
            $oldEdition = $before['service_edition_id'] === null
                ? null : (string)$before['service_edition_id'];
            if ($oldAlbum === $albumId && $oldEdition === $editionId) {
                $this->pdo->commit();
                return false;
            }

            $this->pdo->prepare(
                'UPDATE tracks SET service_album_id=?,service_edition_id=? WHERE id=?'
            )->execute([$albumId, $editionId, $trackDatabaseId]);

            $this->pdo->prepare(
                'INSERT INTO audit_log
                 (admin_id,action,entity_type,entity_id,reason,before_json,after_json)
                 VALUES (?,?,?,?,?,?,?)'
            )->execute([
                $adminId,
                'track_native_identity_updated',
                'track',
                $trackDatabaseId,
                'Owner-attested exact native Yandex track identity',
                json_encode(['album_id'=>$oldAlbum,'edition_id'=>$oldEdition], JSON_THROW_ON_ERROR),
                json_encode(['album_id'=>$albumId,'edition_id'=>$editionId], JSON_THROW_ON_ERROR),
            ]);
            $this->pdo->commit();
            return true;
        } catch (\Throwable $error) {
            if ($this->pdo->inTransaction()) $this->pdo->rollBack();
            throw $error;
        }
    }
}
