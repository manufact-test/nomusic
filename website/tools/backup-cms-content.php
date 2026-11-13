<?php
declare(strict_types=1);
/**
 * Offline website content backup only, NEVER an HTTP route. Does not store
 * users/password hashes or audit logs, and must NOT be treated as a complete
 * disaster-recovery dump. Store the backup encrypted at rest off the server.
 *
 * php website/tools/backup-cms-content.php /private/backup-dir /private/media-dir /private/public-root
 * php website/tools/backup-cms-content.php --verify /private/backup.json
 */
if(PHP_SAPI!=='cli')exit(2);
require dirname(__DIR__).'/app/bootstrap.php';
try {
    if($argc===3 && $argv[1]==='--verify') {
        $details=\Celikom\Website\CmsBackup::inspect($argv[2]);
        echo json_encode($details,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE)."\n";
    } elseif($argc===4) {
        $pdo=\Celikom\Website\Database::connect(
            \Celikom\Website\CmsConfig::databaseSettings()
        );
        $file=\Celikom\Website\CmsBackup::export($pdo,$argv[1],$argv[2],$argv[3]);
        echo "Protected content backup created: ".basename($file)."\n";
    } else {
        fwrite(STDERR,"Usage: php backup-cms-content.php DIR MEDIA_DIR PUBLIC_DIR or --verify FILE\n");
        exit(2);
    }
} catch(\Throwable $e) {
    fwrite(STDERR,"CMS backup unavailable or verification refused\n");
    exit(1);
}
