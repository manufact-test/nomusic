<?php
declare(strict_types=1);
namespace Celikom\Website;

/**
 * Hostinger-only owner-review marker. Requires whole-domain HTTP Basic Auth.
 * This is never production publication approval.
 */
final class CmsStagingGate
{
    private const MARKER = "<?php\nreturn 'CELIKOM_PRIVATE_OWNER_REVIEW_ONLY';\n";

    public static function approved(string $privateAppDirectory): bool
    {
        $app = realpath($privateAppDirectory);
        if (!is_string($app) || !is_dir($app)) return false;
        $file = $app.'/staging-approved.php';
        if (!is_file($file) || is_link($file)) return false;
        clearstatcache(true, $file);
        $mode = fileperms($file);
        if (filesize($file) !== strlen(self::MARKER)
            || !is_int($mode) || ($mode & 0077) !== 0) return false;
        $bytes = file_get_contents($file);
        return is_string($bytes) && hash_equals(self::MARKER, $bytes);
    }
}
