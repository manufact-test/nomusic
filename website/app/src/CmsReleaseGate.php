<?php
declare(strict_types=1);
namespace Celikom\Website;

/**
 * A PRIVATE, operator-created Stage 10 authorization token.
 *
 * A file merely named "release-approved.php" must never unlock the website.
 * Inspect the exact static contents as DATA, do NOT include/evaluate that PHP
 * file. There is no authoring endpoint and no approval artifact in Git.
 *
 * This only checks the final authorization marker. It does not replace the
 * separate backups, rights review, staging QA, DB migration, or owner signoff.
 */
final class CmsReleaseGate
{
    private const MARKER = "<?php\nreturn 'CELIKOM_SITE_AND_CMS_APPROVED_STAGE10';\n";

    public static function approved(string $privateAppDirectory): bool
    {
        $app = realpath($privateAppDirectory);
        if (!is_string($app) || !is_dir($app)) {
            return false;
        }
        $file = $app.'/release-approved.php';
        if (!is_file($file) || is_link($file)) {
            return false;
        }
        clearstatcache(true,$file);
        $size = filesize($file);
        $mode = fileperms($file);
        if ($size !== strlen(self::MARKER) || !is_int($mode) ||
            ($mode & 0077) !== 0) {
            return false;
        }
        $bytes = file_get_contents($file);
        return is_string($bytes) && hash_equals(self::MARKER,$bytes);
    }
}
