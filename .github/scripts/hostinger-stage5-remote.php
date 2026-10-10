<?php
declare(strict_types=1);
// CLI-only Hostinger stage 5 owner operations. No tokens, SQL or media in stdout.
ini_set('display_errors', '0');
if (PHP_SAPI !== 'cli' || count($argv) !== 2) exit(2);
try {
    $site = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com';
    $app = $site . '/celikom';
    $shared = $app . '/shared';
    $release = realpath($app . '/current');
    if ($release === false || !is_link($app . '/current')
        || !str_starts_with($release, $app . '/releases/')
        || is_link($app) || is_link($shared) || is_link($shared . '/env')
        || is_link($shared . '/audio') || !is_file($shared . '/env')
        || realpath($shared . '/audio') !== $shared . '/audio'
        || !is_dir($site . '/public_html')) throw new RuntimeException('layout');
    $requestPath = realpath($argv[1]);
    if ($requestPath === false || !str_starts_with($requestPath, $app . '/incoming/stage5-')
        || basename($requestPath) !== 'hostinger-stage5-request.json'
        || filesize($requestPath) > 1024) throw new RuntimeException('request-path');
    $request = json_decode((string) file_get_contents($requestPath), true, 8, JSON_THROW_ON_ERROR);
    if (!is_array($request) || array_keys($request) !== ['operation']
        || !in_array($request['operation'], ['audit', 'snapshot', 'restore-drill', 'restore-export'], true)) throw new RuntimeException('request');
    $operation = $request['operation'];
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['environment'] !== 'production' || !$config['api_enabled']
        || $config['analytics_enabled'] || $config['storage_driver'] !== 'local'
        || realpath($config['storage_path']) !== $shared . '/audio') throw new RuntimeException('flags');
    $pdo = Celikom\Database\Connection::open($config);
    $approved = (new Celikom\Repositories\PdoCatalogRepository($pdo))->findActive('yandex', '144530503');
    if ($approved === null || (int) $approved['replacement_id'] !== 1
        || (int) $approved['duration_ms'] !== 180872) throw new RuntimeException('mapping');
    // Stage 9 preservation gate: never auto-moderate the real or synthetic pending records.
    $pendingCheck = $pdo->prepare("SELECT COUNT(*)
        FROM track_replacements r JOIN tracks t ON t.id = r.track_id
        WHERE r.id = ? AND r.status = 'pending' AND r.is_active = 0
          AND t.service = 'yandex' AND t.service_track_id = ?");
    foreach ([[2, '799133075'], [3, '38436680']] as [$replacementId, $serviceTrackId]) {
        $pendingCheck->execute([$replacementId, $serviceTrackId]);
        if ((int)$pendingCheck->fetchColumn() !== 1) throw new RuntimeException('protected-pending-changed');
    }
    $key = (string) $approved['storage_key'];
    $store = new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    if (!$store->exists($key) || $store->getSize($key) !== (int) $approved['size_bytes']) throw new RuntimeException('missing-audio');
    $handle = $store->openStream($key);
    $hash = hash_init('sha256');
    while (!feof($handle)) {
        $chunk = fread($handle, 65536);
        if ($chunk === false) throw new RuntimeException('audio-read');
        hash_update($hash, $chunk);
    }
    fclose($handle);
    if (!hash_equals((string) $approved['sha256'], hash_final($hash))) throw new RuntimeException('audio-hash');
    $envHash = hash_file('sha256', $shared . '/env');
    if ($envHash === false || (fileperms($shared . '/env') & 0077)) throw new RuntimeException('env-permissions');

    $backupRoot = $app . '/backups/stage5';
    if (is_link($app . '/backups') || is_link($backupRoot)) throw new RuntimeException('backup-layout');
    $walk = static function(string $dir, string $base): array {
        $result = [];
        $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS));
        foreach ($it as $entry) {
            if ($entry->isLink() || !$entry->isFile()) throw new RuntimeException('unsafe-audio-object');
            $relative = substr($entry->getPathname(), strlen($base) + 1);
            if ($relative === '' || str_contains($relative, '..') || count($result) >= 2000)
                throw new RuntimeException('unsafe-audio-path');
            $result[$relative] = ['sha256' => hash_file('sha256', $entry->getPathname()), 'size' => $entry->getSize()];
        }
        ksort($result);
        return $result;
    };
    $audio = $walk($shared . '/audio', $shared . '/audio');
    if (!$audio || array_sum(array_column($audio, 'size')) > 500 * 1024 * 1024) throw new RuntimeException('backup-size-limit');
    if ($operation === 'audit') {
        $prior = glob($backupRoot . '/snapshot-*', GLOB_ONLYDIR) ?: [];
        if (!$prior) throw new RuntimeException('no-snapshot');
        rsort($prior, SORT_STRING);
        if (is_link($prior[0]) || !is_file($prior[0] . '/manifest.json'))
            throw new RuntimeException('snapshot-layout');
        $baseline = json_decode((string) file_get_contents($prior[0] . '/manifest.json'), true, 16, JSON_THROW_ON_ERROR);
        if (($baseline['format'] ?? null) !== 1 || !hash_equals((string) $baseline['env_sha256'], $envHash)
            || ($baseline['files'] ?? null) !== $audio) throw new RuntimeException('state-changed-after-deploy');
        foreach ($baseline['tables'] as $table => $beforeCount) {
            if (!in_array($table, ['schema_migrations', 'tracks', 'audio_assets', 'track_replacements',
                'analytics_events', 'analytics_daily_aggregates', 'audio_fingerprint_jobs',
                'upload_submissions', 'track_requests', 'upload_rate_buckets',
                'admins', 'admin_sessions', 'admin_login_attempts', 'audit_log',
                'track_request_reviews', 'reports', 'users', 'user_devices', 'user_sessions',
                'user_auth_attempts', 'user_auth_events', 'user_email_security'], true)) throw new RuntimeException('unknown_table');
            $currentCount = (int) $pdo->query('SELECT COUNT(*) FROM ' . chr(96) . $table . chr(96))->fetchColumn();
            // The only permitted pre-deployment row-count increase is the
            // expected checksummed additive Stage 9 email security migration.
            if ($table === 'schema_migrations' && $currentCount === (int) $beforeCount + 1) {
                $migration = $pdo->prepare('SELECT sha256 FROM schema_migrations WHERE version = ?');
                $migrationFile = '005_email_security.sql';
                $migration->execute([$migrationFile]);
                $checksum = $migration->fetchColumn();
                $diskChecksum = hash_file('sha256', $release . '/migrations/' . $migrationFile);
                if (!is_string($checksum) || !is_string($diskChecksum)
                    || !hash_equals($checksum, $diskChecksum)) throw new RuntimeException('unexpected_migration');
                continue;
            }
            if ($currentCount !== (int) $beforeCount)
                throw new RuntimeException('database-row-count-changed');
        }
        echo "Stage 9 after-deploy audit PASS: private env, media and historic row counts preserved; additive Stage 9 email-security migration verified.\n";
        exit(0);
    }
    $copyAudio = static function(string $source, string $destination, array $index): void {
        foreach ($index as $relative => $data) {
            $from = $source . '/' . $relative;
            $to = $destination . '/' . $relative;
            if (!is_dir(dirname($to)) && !mkdir(dirname($to), 0700, true)) throw new RuntimeException('copy-directory');
            if (is_link($from) || !copy($from, $to)) throw new RuntimeException('copy-file');
            chmod($to, 0600);
            if (filesize($to) !== $data['size'] || !hash_equals($data['sha256'], hash_file('sha256', $to)))
                throw new RuntimeException('copy-integrity');
        }
    };
    $latest = static function() use ($backupRoot): string {
        $paths = glob($backupRoot . '/snapshot-*', GLOB_ONLYDIR) ?: [];
        rsort($paths, SORT_STRING);
        if (!$paths || is_link($paths[0]) || realpath($paths[0]) !== $paths[0])
            throw new RuntimeException('no-snapshot');
        return $paths[0];
    };
    $verify = static function(string $dir): array {
        if (is_link($dir) || !is_file($dir . '/manifest.json') || !is_file($dir . '/database.sql')
            || !is_file($dir . '/env') || is_link($dir . '/env') || is_link($dir . '/database.sql'))
            throw new RuntimeException('snapshot-layout');
        $data = json_decode((string) file_get_contents($dir . '/manifest.json'), true, 16, JSON_THROW_ON_ERROR);
        if (!is_array($data) || ($data['format'] ?? null) !== 1 || !is_array($data['files'] ?? null)
            || !hash_equals((string) $data['env_sha256'], hash_file('sha256', $dir . '/env'))
            || !hash_equals((string) $data['sql_sha256'], hash_file('sha256', $dir . '/database.sql')))
            throw new RuntimeException('snapshot-hash');
        foreach ($data['files'] as $name => $file) {
            $path = $dir . '/audio/' . $name;
            if ($name === '' || str_contains($name, '..') || is_link($path)
                || !is_file($path) || filesize($path) !== $file['size']
                || !hash_equals($file['sha256'], hash_file('sha256', $path)))
                throw new RuntimeException('snapshot-audio-hash');
        }
        return $data;
    };
    if ($operation === 'snapshot') {
        if (!is_dir($backupRoot) && !mkdir($backupRoot, 0700, true)) throw new RuntimeException('backup-root');
        chmod($backupRoot, 0700);
        $id = gmdate('YmdTHis') . '-' . bin2hex(random_bytes(6));
        $staging = $backupRoot . '/.partial-' . $id;
        $final = $backupRoot . '/snapshot-' . $id;
        if (!mkdir($staging, 0700)) throw new RuntimeException('snapshot-dir');
        mkdir($staging . '/audio', 0700);
        if (!copy($shared . '/env', $staging . '/env')) throw new RuntimeException('snapshot-env');
        chmod($staging . '/env', 0600);
        $copyAudio($shared . '/audio', $staging . '/audio', $audio);
        // SQL export of the CELIKOM-owned tables with schema and explicit IDs.
        // Generated columns are reconstructed by MySQL; they are never inserted.
        $stream = fopen($staging . '/database.sql', 'xb');
        if ($stream === false) throw new RuntimeException('snapshot-sql');
        chmod($staging . '/database.sql', 0600);
        // Include every existing Stage 7 table: the old six-table snapshot is insufficient.
        $tables = ['schema_migrations', 'tracks', 'audio_assets', 'track_replacements',
            'analytics_events', 'analytics_daily_aggregates', 'audio_fingerprint_jobs',
            'upload_submissions', 'track_requests', 'upload_rate_buckets'];
        // Later private snapshots also protect Stage 8 moderation state. Pre-deployment
        // snapshots correctly omit these tables until migration 003 exists.
        $optional = ['admins', 'admin_sessions', 'admin_login_attempts', 'audit_log',
            'track_request_reviews', 'reports', 'users', 'user_devices', 'user_sessions',
            'user_auth_attempts', 'user_auth_events', 'user_email_security'];
        $present = $pdo->prepare('SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = ?');
        foreach ($optional as $extra) {
            $present->execute([$extra]);
            if ((int) $present->fetchColumn() === 1) $tables[] = $extra;
        }
        $counts = [];
        $quoteName = static fn(string $value): string => chr(96) . $value . chr(96);
        $pdo->beginTransaction();
        try {
            fwrite($stream, "SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS=0;\n");
            foreach ($tables as $table) {
                $structure = $pdo->query('SHOW CREATE TABLE ' . $quoteName($table))->fetch(PDO::FETCH_NUM);
                if (!$structure || !isset($structure[1])) throw new RuntimeException('snapshot-schema');
                fwrite($stream, $structure[1] . ";\n");
            }
            foreach ($tables as $table) {
                $columns = [];
                foreach ($pdo->query('SHOW FULL COLUMNS FROM ' . $quoteName($table)) as $field) {
                    if (!str_contains(strtoupper((string) ($field['Extra'] ?? '')), 'GENERATED'))
                        $columns[] = $field['Field'];
                }
                $colNames = implode(', ', array_map($quoteName, $columns));
                $rows = $pdo->query('SELECT ' . $colNames . ' FROM ' . $quoteName($table));
                $count = 0;
                while ($row = $rows->fetch(PDO::FETCH_ASSOC)) {
                    $values = array_map(static fn($value): string =>
                        $value === null ? 'NULL' : $pdo->quote((string) $value), array_values($row));
                    fwrite($stream, 'INSERT INTO ' . $quoteName($table) . ' (' . $colNames .
                        ') VALUES (' . implode(', ', $values) . ");\n");
                    $count++;
                }
                $counts[$table] = $count;
                $rows->closeCursor();
            }
            fwrite($stream, "SET FOREIGN_KEY_CHECKS=1;\n");
            $pdo->commit();
        } catch (Throwable $e) {
            if ($pdo->inTransaction()) $pdo->rollBack();
            throw $e;
        } finally {
            fclose($stream);
        }
        $manifest = ['format'=>1, 'created_at'=>gmdate('c'), 'env_sha256'=>$envHash,
            'sql_sha256'=>hash_file('sha256', $staging . '/database.sql'),
            'files'=>$audio, 'tables'=>$counts];
        file_put_contents($staging . '/manifest.json',
            json_encode($manifest, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR), LOCK_EX);
        chmod($staging . '/manifest.json', 0600);
        $verify($staging);
        if (!rename($staging, $final)) throw new RuntimeException('snapshot-publish');
        echo "Stage 5 private snapshot PASS: copied ", count($audio), " audio objects and ",
            count($tables), " SQL tables; credentials and media remain outside the web root.\n";
        exit(0);
    }
    $backup = $latest();
    $manifest = $verify($backup);
    if ($operation === 'restore-export') {
        // stdout is raw SQL, caller must redirect to private runner scratch.
        readfile($backup . '/database.sql');
        exit(0);
    }
    if ($operation === 'restore-drill') {
        $scratch = $backupRoot . '/.drill-' . bin2hex(random_bytes(8));
        if (!mkdir($scratch, 0700)) throw new RuntimeException('drill-dir');
        mkdir($scratch . '/audio', 0700);
        if (!copy($backup . '/env', $scratch . '/env')) throw new RuntimeException('drill-env');
        chmod($scratch . '/env', 0600);
        $copyAudio($backup . '/audio', $scratch . '/audio', $manifest['files']);
        if (!hash_equals($manifest['env_sha256'], hash_file('sha256', $scratch . '/env'))
            || $walk($scratch . '/audio', $scratch . '/audio') !== $manifest['files'])
            throw new RuntimeException('drill-integrity');
        $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($scratch, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
        foreach ($it as $entry) { if ($entry->isDir()) rmdir($entry->getPathname()); else unlink($entry->getPathname()); }
        rmdir($scratch);
        echo "Stage 5 isolated file restore PASS: config and ", count($manifest['files']),
            " audio objects restored and verified; live deployment untouched.\n";
        exit(0);
    }
} catch (Throwable $e) {
    fwrite(STDERR, "Stage 5 operation failed safely (" .
        (in_array($e->getMessage(), ['no-snapshot', 'backup-size-limit', 'flags', 'layout'], true)
            ? $e->getMessage() : 'integrity-or-precondition-check') . "). No private data logged.\n");
    exit(1);
}
