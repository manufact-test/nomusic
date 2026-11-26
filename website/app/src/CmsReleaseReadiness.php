<?php
declare(strict_types=1);
namespace Celikom\Website;

use PDO;
use RuntimeException;

/**
 * Read-only Stage 10 CMS readiness audit. NEVER authorizes release.
 * Missing evidence must stay visible as a blocker rather than being guessed.
 * Production deployment still needs independent backup/restore, visual,
 * legal/rights, HTTPS and owner review.
 */
final class CmsReleaseReadiness
{
    private const V10_BLOB = 'ece0795ff0a007fd41f361af1838837b7efd2d71';

    /**
     * @return array{ready:bool,checks:array<string,bool>,blockers:list<string>,revision_id:int|null}
     */
    public static function inspect(
        PDO $pdo, string $appDir, string $seedFile, string $publicRoot,
        ?string $ownerApprovedPopupSha = null
    ): array {
        $checks = [];
        $blockers = [];
        $app = realpath($appDir);
        $public = realpath($publicRoot);
        $seed = realpath($seedFile);
        if (!is_string($app) || !is_string($public) || !is_string($seed) ||
            !is_dir($app) || !is_dir($public) || !is_file($seed) ||
            str_starts_with($app, $public.'/') ||
            str_starts_with($public, $app.'/') || $app === $public) {
            throw new RuntimeException('Invalid private CMS/public filesystem boundary');
        }
        $templatePath = $app.'/Templates/site-v10.html';
        $manifestPath = $app.'/Config/content-fields-v10.json';
        if (!is_file($templatePath) || is_link($templatePath) ||
            !is_file($manifestPath) || is_link($manifestPath) ||
            is_link($seedFile)) {
            throw new RuntimeException('Approved template, manifest or FAQ seed unavailable');
        }
        $template = file_get_contents($templatePath);
        $manifest = file_get_contents($manifestPath);
        $faq = file_get_contents($seed);
        if (!is_string($template) || !is_string($manifest) || !is_string($faq)) {
            throw new RuntimeException('Cannot read approved source documents');
        }
        $blob = sha1('blob '.strlen($template)."\0".$template);
        $checks['approved_v10_template'] = hash_equals(self::V10_BLOB, $blob);
        if (!$checks['approved_v10_template']) {
            $blockers[] = 'approved_v10_template_changed';
        }

        // Every one of the editor's fields and FAQ must remain valid. A broken
        // draft may not become the published version during release.
        try {
            $draft = CmsDraftStore::get($pdo);
            CmsEditor::validate($template, $manifest, $faq, [
                'content'=>$draft['content'],
                'faq'=>$draft['faq'],
            ]);
            $checks['draft_is_valid'] = true;
        } catch (\Throwable $e) {
            $checks['draft_is_valid'] = false;
            $blockers[] = 'cms_draft_invalid';
        }

        $active = (int)$pdo->query('SELECT COUNT(*) FROM admin_users WHERE is_active=1')
            ->fetchColumn();
        $checks['active_owner_exists'] = $active === 1;
        if (!$checks['active_owner_exists']) {
            $blockers[] = 'cms_owner_missing_or_ambiguous';
        }

        $published = CmsRevisions::publishedId($pdo);
        $checks['published_revision_exists'] = $published !== null && $published > 0;
        if (!$checks['published_revision_exists']) {
            $blockers[] = 'cms_published_revision_missing';
        } elseif ($checks['approved_v10_template']) {
            try {
                $page = CmsRevisions::publishedPage($pdo, $template, $manifest, $faq);
                if (!str_contains($page, '/media/celikom-popup-approved.png')) {
                    throw new RuntimeException('Required reviewed popup slot missing');
                }
                $checks['published_revision_valid'] = true;
            } catch (\Throwable $e) {
                $checks['published_revision_valid'] = false;
                $blockers[] = 'cms_published_revision_invalid';
            }
        } else {
            $checks['published_revision_valid'] = false;
            $blockers[] = 'cms_published_revision_not_checked';
        }

        // The popup must be provisioned separately, after rights/redaction
        // signoff. Never import private uploads directly or embed screenshots
        // into GitHub. A correct SHA is not evidence of ownership by itself.
        $expected = is_string($ownerApprovedPopupSha) &&
            preg_match('/^[a-f0-9]{64}$/D', $ownerApprovedPopupSha) === 1
            ? $ownerApprovedPopupSha : null;
        $file = $public.'/media/celikom-popup-approved.png';
        $validPopup = false;
        if ($expected !== null && is_file($file) && !is_link($file)) {
            $size = filesize($file);
            if (is_int($size) && $size >= 30 && $size <= CmsMediaStore::MAX_BYTES) {
                $bytes = file_get_contents($file);
                if (is_string($bytes) && strlen($bytes) === $size &&
                    hash_equals($expected, hash('sha256', $bytes))) {
                    $dimensions = @getimagesizefromstring($bytes);
                    $validPopup = (new \finfo(FILEINFO_MIME_TYPE))->buffer($bytes) === 'image/png'
                        && is_array($dimensions)
                        && ($dimensions['mime'] ?? null) === 'image/png'
                        && ($dimensions[0] ?? 0) > 0
                        && ($dimensions[1] ?? 0) > 0
                        && ($dimensions[0] ?? 9999) <= 4096
                        && ($dimensions[1] ?? 9999) <= 4096;
                }
            }
        }
        $checks['owner_reviewed_popup_bytes_match'] = $validPopup;
        if (!$validPopup) $blockers[] = 'approved_popup_bytes_or_review_missing';

        // These require an actual Stage 10 operator-reviewed drill and
        // cannot be inferred from a CMS content backup or CI-only rehearsal.
        $checks['full_database_backup_and_restore_verified'] = false;
        $checks['production_file_rollback_verified'] = false;
        $checks['final_owner_joint_release_consent'] = false;
        $blockers[] = 'full_database_backup_and_restore_pending';
        $blockers[] = 'production_file_rollback_pending';
        $blockers[] = 'owner_joint_release_approval_pending';

        return [
            'ready'=>false,
            'checks'=>$checks,
            'blockers'=>$blockers,
            'revision_id'=>$published,
        ];
    }
}
