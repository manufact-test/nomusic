<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use PDO;
use RuntimeException;

/**
 * Stage 9 draft persistence for a single admin site editor.
 * One JSON document, one monotonic optimistic version; never publishes.
 * All edits MUST be independently validated before they reach this class.
 */
final class CmsDraftStore
{
    public static function get(PDO $pdo): array
    {
        $q = $pdo->query('SELECT draft_json,optimistic_version FROM content_drafts WHERE id=1');
        $row = $q->fetch(PDO::FETCH_ASSOC);
        if (!$row) {
            return ['version'=>0, 'content'=>[], 'faq'=>[]];
        }
        $raw = json_decode((string)$row['draft_json'], true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($raw) || !isset($raw['content'],$raw['faq']) ||
            !is_array($raw['content']) || !is_array($raw['faq'])) {
            throw new RuntimeException('Invalid saved draft record');
        }
        return ['version'=>(int)$row['optimistic_version'],
            'content'=>$raw['content'],'faq'=>$raw['faq']];
    }

    /**
     * Save a verified canonical full snapshot. Returns new version on
     * success; stale clients receive null. Never silently lose prior edits.
     */
    public static function save(PDO $pdo, int $adminId, int $expected, array $draft): ?int
    {
        if ($adminId < 1 || $expected < 0 || $expected >= PHP_INT_MAX ||
            array_keys($draft) !== ['content','faq'] ||
            !is_array($draft['content']) || !is_array($draft['faq']) ||
            (array_is_list($draft['content']) && $draft['content'] !== []) ||
            (array_is_list($draft['faq']) && $draft['faq'] !== [])) {
            throw new InvalidArgumentException('Invalid draft snapshot');
        }
        $payload = json_encode($draft,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
        if (strlen($payload) > 131072) throw new InvalidArgumentException('Draft too large');
        try {
            $pdo->beginTransaction();
            // Materialize the singleton row atomically without changing a
            // previously existing draft (it is the sole editor document).
            $pdo->prepare(
                "INSERT IGNORE INTO content_drafts (id,draft_json,optimistic_version,updated_by) " .
                "VALUES (1,'{\"content\":{},\"faq\":{}}',0,?)"
            )->execute([$adminId]);
            $read = $pdo->query('SELECT optimistic_version FROM content_drafts WHERE id=1 FOR UPDATE');
            $current = $read->fetchColumn();
            if ($current === false || (int)$current !== $expected) {
                $pdo->rollBack();
                return null;
            }
            $pdo->prepare(
                'UPDATE content_drafts SET draft_json=?,optimistic_version=?,updated_by=? WHERE id=1'
            )->execute([$payload,$expected+1,$adminId]);
            $pdo->prepare(
                'INSERT INTO audit_log (actor_admin_id,event_name,subject_key,event_metadata) VALUES (?,?,?,?)'
            )->execute([$adminId,'cms.draft.saved','site',json_encode(['version'=>$expected+1],JSON_THROW_ON_ERROR)]);
            $pdo->commit();
            return $expected + 1;
        } catch (\Throwable $e) {
            if ($pdo->inTransaction()) $pdo->rollBack();
            throw $e;
        }
    }
}
