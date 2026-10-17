<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use PDO;
use RuntimeException;

/**
 * Stage 9 revision backend for the site ONLY. Each publication stores an
 * immutable, fully verified snapshot and swaps a single pointer atomically.
 * This class does not bypass the Stage 10 deployment/release gate and is not
 * connected to any public website request yet.
 */
final class CmsRevisions
{
    /** @return int|null */
    public static function publishedId(PDO $pdo): ?int
    {
        $id=$pdo->query('SELECT published_revision_id FROM site_state WHERE id=1')->fetchColumn();
        return $id === false || $id === null ? null : (int)$id;
    }

    /**
     * Take the current shared draft. Optimistic version protects against
     * accidentally publishing content saved in another browser tab.
     */
    public static function publish(
        PDO $pdo, int $adminId, int $expectedDraftVersion, string $note,
        string $template, string $manifest, string $faqSeed
    ): ?int {
        self::checkActorAndNote($adminId,$note);
        if ($expectedDraftVersion < 1) throw new InvalidArgumentException('No saved draft to publish');
        try {
            $pdo->beginTransaction();
            $state=$pdo->query('SELECT published_revision_id FROM site_state WHERE id=1 FOR UPDATE')->fetchColumn();
            // site_state id=1 MUST exist; row factory from migration 001.
            if ($state === false && $pdo->query('SELECT COUNT(*) FROM site_state WHERE id=1')->fetchColumn() == 0) {
                throw new RuntimeException('CMS state row missing');
            }
            $stmt=$pdo->query('SELECT draft_json,optimistic_version FROM content_drafts WHERE id=1 FOR UPDATE');
            $row=$stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row || (int)$row['optimistic_version'] !== $expectedDraftVersion) {
                $pdo->rollBack();
                return null;
            }
            $draft=json_decode((string)$row['draft_json'],true,512,JSON_THROW_ON_ERROR);
            $snapshot=self::encodeVerifiedSnapshot($draft,$template,$manifest,$faqSeed);
            $id=self::insertRevision($pdo,$adminId,$note,$snapshot);
            self::pointTo($pdo,$id,$adminId);
            self::audit($pdo,$adminId,'cms.revision.published',$id,[
                'draft_version'=>$expectedDraftVersion
            ]);
            $pdo->commit();
            return $id;
        } catch (\Throwable $e) {
            if($pdo->inTransaction())$pdo->rollBack();
            throw $e;
        }
    }

    /**
     * Restore always creates a NEW immutable revision, retaining a history
     * trail. The expected live revision guards concurrent owner tabs.
     */
    public static function restore(
        PDO $pdo,int $adminId,int $targetId,?int $expectedPublishedId,
        string $note,string $template,string $manifest,string $faqSeed
    ): ?int {
        self::checkActorAndNote($adminId,$note);
        if($targetId<1 || $expectedPublishedId===null || $expectedPublishedId<1) {
            throw new InvalidArgumentException('Select an existing published revision');
        }
        try {
            $pdo->beginTransaction();
            $row=$pdo->query('SELECT published_revision_id FROM site_state WHERE id=1 FOR UPDATE')
                ->fetch(PDO::FETCH_ASSOC);
            if(!$row || $row['published_revision_id']===null) {
                throw new RuntimeException('No published CMS state to restore');
            }
            if((int)$row['published_revision_id']!==$expectedPublishedId) {
                $pdo->rollBack();
                return null;
            }
            $read=$pdo->prepare('SELECT snapshot_json FROM content_revisions WHERE id=?');
            $read->execute([$targetId]);
            $raw=$read->fetchColumn();
            if(!is_string($raw))throw new InvalidArgumentException('Unknown revision');
            $previous=self::decodeVerifiedSnapshot($raw,$template,$manifest,$faqSeed);
            $snapshot=self::encodeVerifiedSnapshot($previous,$template,$manifest,$faqSeed);
            $newId=self::insertRevision($pdo,$adminId,$note,$snapshot);
            self::pointTo($pdo,$newId,$adminId);
            self::audit($pdo,$adminId,'cms.revision.restored',$newId,[
                'source_revision_id'=>$targetId,'previous_revision_id'=>$expectedPublishedId
            ]);
            $pdo->commit();
            return $newId;
        } catch (\Throwable $e) {
            if($pdo->inTransaction())$pdo->rollBack();
            throw $e;
        }
    }

    /** Read the pointer and snapshot in ONE SQL statement; no draft mixing. */
    public static function publishedPage(
        PDO $pdo,string $template,string $manifest,string $faqSeed
    ): string {
        $row=$pdo->query(
            'SELECT s.published_revision_id,r.snapshot_json FROM site_state s ' .
            'LEFT JOIN content_revisions r ON r.id=s.published_revision_id WHERE s.id=1'
        )->fetch(PDO::FETCH_ASSOC);
        if(!$row)throw new RuntimeException('Missing website publication state');
        if($row['published_revision_id']===null) {
            return CmsEditor::validate($template,$manifest,$faqSeed,['content'=>[],'faq'=>[]]);
        }
        if(!is_string($row['snapshot_json']))throw new RuntimeException('Missing published snapshot');
        $draft=self::decodeVerifiedSnapshot($row['snapshot_json'],$template,$manifest,$faqSeed);
        return CmsEditor::validate($template,$manifest,$faqSeed,$draft);
    }

    private static function encodeVerifiedSnapshot(
        mixed $draft,string $template,string $manifest,string $faqSeed
    ): string {
        if(!is_array($draft))throw new InvalidArgumentException('Invalid revision content');
        CmsEditor::validate($template,$manifest,$faqSeed,$draft);
        $data=[
            'format'=>1,
            'template_sha'=>sha1('blob '.strlen($template)."\0".$template),
            'manifest_sha'=>hash('sha256',$manifest),
            'content'=>$draft['content'],
            'faq'=>$draft['faq'],
        ];
        return json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
    }

    /** @return array{content:array,faq:array} */
    private static function decodeVerifiedSnapshot(
        string $raw,string $template,string $manifest,string $faqSeed
    ): array {
        $data=json_decode($raw,true,512,JSON_THROW_ON_ERROR);
        if(!is_array($data) || array_keys($data)!==[
            'format','template_sha','manifest_sha','content','faq'
        ] || $data['format']!==1 ||
            !is_string($data['template_sha']) ||
            !hash_equals(sha1('blob '.strlen($template)."\0".$template),$data['template_sha']) ||
            !is_string($data['manifest_sha']) ||
            !hash_equals(hash('sha256',$manifest),$data['manifest_sha'])) {
            throw new RuntimeException('Revision is not compatible with approved v10');
        }
        $draft=['content'=>$data['content'],'faq'=>$data['faq']];
        CmsEditor::validate($template,$manifest,$faqSeed,$draft);
        return $draft;
    }

    private static function insertRevision(PDO $pdo,int $adminId,string $note,string $snapshot): int
    {
        $pdo->prepare(
            'INSERT INTO content_revisions(snapshot_json,change_note,created_by) VALUES(?,?,?)'
        )->execute([$snapshot,$note,$adminId]);
        $id=(int)$pdo->lastInsertId();
        if($id<1)throw new RuntimeException('Revision creation failed');
        return $id;
    }

    private static function pointTo(PDO $pdo,int $id,int $adminId): void
    {
        $change=$pdo->prepare(
            'UPDATE site_state SET published_revision_id=?,updated_by=? WHERE id=1'
        );
        $change->execute([$id,$adminId]);
        if($change->rowCount()!==1)throw new RuntimeException('Publication pointer did not change');
    }

    private static function audit(PDO $pdo,int $adminId,string $event,int $subject,array $details): void
    {
        $pdo->prepare(
            'INSERT INTO audit_log(actor_admin_id,event_name,subject_key,event_metadata) VALUES(?,?,?,?)'
        )->execute([$adminId,$event,(string)$subject,json_encode($details,JSON_THROW_ON_ERROR)]);
    }

    private static function checkActorAndNote(int $id,string $note): void
    {
        if($id<1 || preg_match('//u',$note)!==1 ||
            strlen($note)>1020 || preg_match_all('/./us',$note)>255 ||
            preg_match('/[\x00-\x1F\x7F]/',$note)) {
            throw new InvalidArgumentException('Invalid CMS revision author or note');
        }
    }
}
