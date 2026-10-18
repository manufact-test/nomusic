<?php
declare(strict_types=1);
/**
 * Stage 10 offline owner-only coordinated capture (NOT deployment).
 *
 * Environment:
 *   CELIKOM_SITE_WRITE_GATE_FILE=/private/.celikom-cms-writes.lock
 *   CELIKOM_SITE_FULL_BACKUP_KEY=(independent base64 32-byte key)
 *   CELIKOM_SITE_DB_*=(dedicated website DB only)
 *
 * php website/tools/backup-coordinated-cms.php PRIVATE_BUNDLE_DIR PRIVATE_MEDIA_DIR PUBLIC_DIR
 * php website/tools/backup-coordinated-cms.php --verify PRIVATE_MANIFEST PUBLIC_DIR
 *
 * The content+media JSON remains unencrypted and must NOT be copied offsite
 * without separate encryption. All CMS data writers and media GC must obey
 * the same gate. No production workflow invokes this tool.
 */
if (PHP_SAPI !== 'cli') exit(2);
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsConfig;
use Celikom\Website\CmsConsistentBackup;
use Celikom\Website\CmsFullDbBackup;
use Celikom\Website\CmsWriteQuiescence;
use Celikom\Website\Database;

try {
    $key = CmsFullDbBackup::keyFromEnv();
    if ($argc === 4 && $argv[1] !== '--verify') {
        $gate = CmsWriteQuiescence::snapshot($argv[3]);
        try {
            $db = Database::connect(CmsConfig::databaseSettings());
            $result = CmsConsistentBackup::capture(
                $db, $argv[1], $argv[2], $argv[3], $key, $gate
            );
            echo json_encode([
                'manifest' => basename($result['manifest']),
                'verified' => $result['report']['consistent'],
                'media_files' => $result['report']['media_files'],
            ], JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES)."\n";
        } finally {
            $gate->release();
        }
    } elseif ($argc === 4 && $argv[1] === '--verify') {
        $report = CmsConsistentBackup::inspect($argv[2], $key, $argv[3]);
        echo json_encode($report, JSON_THROW_ON_ERROR)."\n";
    } else {
        fwrite(STDERR, "Usage: backup-coordinated-cms.php BUNDLE_DIR MEDIA_DIR PUBLIC_DIR OR --verify MANIFEST PUBLIC_DIR\n");
        exit(2);
    }
} catch (\Throwable $error) {
    fwrite(STDERR, "Coordinated CMS snapshot unavailable; no release permitted\n");
    exit(1);
}
