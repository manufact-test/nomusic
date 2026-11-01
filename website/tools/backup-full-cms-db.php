<?php
declare(strict_types=1);
/**
 * Full dedicated CMS database encrypted backup, NEVER a web endpoint.
 * Key is an independent random 32-byte base64 value in:
 * CELIKOM_SITE_FULL_BACKUP_KEY (keep outside files, GitHub and shell history).
 *
 * Requires the website's dedicated CELIKOM_SITE_DB_* settings. Does NOT
 * include private image bytes; combine with the Stage 9 content/media backup
 * and an independently reviewed full restore rehearsal before any release.
 *
 * php website/tools/backup-full-cms-db.php BACKUP_DIR PUBLIC_ROOT
 * php website/tools/backup-full-cms-db.php --verify ENCRYPTED_FILE
 */
if(PHP_SAPI!=='cli')exit(2);
require dirname(__DIR__).'/app/bootstrap.php';
try {
    $key=\Celikom\Website\CmsFullDbBackup::keyFromEnv();
    if($argc===3 && $argv[1]==='--verify') {
        $report=\Celikom\Website\CmsFullDbBackup::inspect($argv[2],$key);
        echo json_encode($report,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES)."\n";
    } elseif($argc===3) {
        $pdo=\Celikom\Website\Database::connect(
            \Celikom\Website\CmsConfig::databaseSettings()
        );
        $file=\Celikom\Website\CmsFullDbBackup::export(
            $pdo,$argv[1],$argv[2],$key
        );
        echo "Encrypted dedicated CMS DB backup verified: ".basename($file)."\n";
    } else {
        fwrite(STDERR,"Usage: backup-full-cms-db.php BACKUP_DIR PUBLIC_ROOT or --verify FILE\n");
        exit(2);
    }
} catch(\Throwable $e) {
    fwrite(STDERR,"Encrypted CMS DB backup unavailable or verification failed; release blocked\n");
    exit(1);
}
