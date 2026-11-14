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
        || !in_array($request['operation'], ['audit', 'snapshot', 'restore-drill', 'restore-export', 'restore-counts'], true)) throw new RuntimeException('request');
    $operation = $request['operation'];
    require $release . '/bootstrap.php';
    $config = require $release . '/config/app.php';
    if ($config['environment'] !== 'production' || !$config['api_enabled']
        || $config['analytics_enabled'] || $config['storage_driver'] !== 'local'
        || realpath($config['storage_path']) !== $shared . '/audio') throw new RuntimeException('flags');
    $pdo = Celikom\Database\Connection::open($config);
    if ($operation === 'snapshot' && class_exists(Celikom\Promo\PromoAdminView::class)) {
        foreach (['codes'=>[false,false],'create'=>[true,false],'activations'=>[false,true]] as $name=>[$create,$activations]) {
            $started=microtime(true);
            $html=(new Celikom\Promo\PromoAdminView($pdo))->render(str_repeat('0',64),1,$create,$activations);
            printf("Promo read-only render diagnostic: %s %.3fs %d bytes\n",$name,microtime(true)-$started,strlen($html));
        }
    }

    // Read-only deployment diagnostics, never SQL, account data or credentials.
    $engine=str_contains((string)$pdo->query('SELECT VERSION()')->fetchColumn(),'MariaDB')?'MariaDB':'MySQL';
    $marker=(int)$pdo->query("SELECT COUNT(*) FROM schema_migrations WHERE version='013_automatic_rewards.sql'")->fetchColumn();
    $column=(int)$pdo->query("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='reward_ledger' AND column_name='grant_mode'")->fetchColumn();
    $allocation=(int)$pdo->query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='reward_allocations'")->fetchColumn();
    if (!in_array($operation, ['restore-export', 'restore-counts'], true))
        fwrite(STDOUT,"Reward schema diagnostic: engine=$engine marker=$marker grant_mode=$column allocations=$allocation\n");
    $approved = (new Celikom\Repositories\PdoCatalogRepository($pdo))->findActive('yandex', '144530503');
    if ($approved === null || (int) $approved['replacement_id'] !== 1
        || (int) $approved['duration_ms'] !== 180872) throw new RuntimeException('mapping');
    // Preserve the identity of legacy records. Their current moderation decisions
    // belong to the owner; backups must also work after manual approval.
    $pendingCheck = $pdo->prepare("SELECT COUNT(*)
        FROM track_replacements r JOIN tracks t ON t.id = r.track_id
        WHERE r.id = ? AND r.status IN ('pending','approved','rejected','disabled')
          AND t.service = 'yandex' AND t.service_track_id = ?");
    foreach ([[2, '799133075'], [3, '38436680']] as [$replacementId, $serviceTrackId]) {
        $pendingCheck->execute([$replacementId, $serviceTrackId]);
        if ((int)$pendingCheck->fetchColumn() !== 1) throw new RuntimeException('protected-record-missing');
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
    $audioBytes = array_sum(array_column($audio, 'size'));
    $freeBytes = @disk_free_space($app);
    // This deployment only changes the application release and additive DB
    // migrations. Existing audio objects are immutable and are never written:
    // LocalStorageAdapter uses temp-file + atomic rename, and W93 sidecars are
    // separate additive files with their own exact rollback. Keep a complete
    // SHA256/size inventory of the existing library instead of duplicating
    // hundreds of MB of MP3s on the shared-hosting quota.
    if (!$audio || $audioBytes > 20 * 1024 * 1024 * 1024 ||
        $freeBytes === false || $freeBytes < 128 * 1024 * 1024) {
        throw new RuntimeException('backup-capacity-limit');
    }
    // Hashing the complete private audio inventory can outlast MariaDB's
    // idle-connection timeout. Reopen the read-only DB connection before
    // continuing with information_schema, audit and snapshot queries.
    unset($pdo);
    $pdo = Celikom\Database\Connection::open($config);
    $pdo->query('SELECT 1')->fetchColumn();
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
                'user_auth_attempts', 'user_auth_events', 'user_email_security', 'entitlement_ledger', 'account_trials',
                'subscriptions','billing_events','billing_payments','billing_adjustments',
                'referrals','referral_codes','reward_ledger','reward_policy','reward_allocations','service_incident_locks','service_incidents','incident_compensations', 'promo_codes', 'promo_redemptions', 'promo_attempt_buckets', 'windows_gain_variants', 'support_tickets', 'support_messages', 'admin_navigation_seen'], true)) throw new RuntimeException('unknown_table');
            $currentCount = (int) $pdo->query('SELECT COUNT(*) FROM ' . chr(96) . $table . chr(96))->fetchColumn();
            // The only permitted pre-deployment row-count increase is the
            // expected checksummed additive Stage 9 email security migration.
            if ($table === 'schema_migrations' && $currentCount > (int)$beforeCount
                && $currentCount <= (int)$beforeCount + 2) {
                // Stage10 permits only the two checksummed additive migrations.
                foreach (glob($release . '/migrations/*.sql') ?: [] as $migrationPath) {
                    $migrationFile = basename($migrationPath);
                    $migration = $pdo->prepare('SELECT sha256 FROM schema_migrations WHERE version = ?');
                    $migration->execute([$migrationFile]);
                    $checksum = $migration->fetchColumn();
                    $diskChecksum = hash_file('sha256', $release . '/migrations/' . $migrationFile);
                    if (!is_string($checksum) || !is_string($diskChecksum)
                        || !hash_equals($checksum, $diskChecksum)) throw new RuntimeException('unexpected_migration');
                }
                continue;
            }
            if ($currentCount !== (int) $beforeCount)
                throw new RuntimeException('database-row-count-changed');
        }
        foreach (['promo_codes','promo_redemptions','promo_attempt_buckets', 'windows_gain_variants', 'support_tickets', 'support_messages'] as $table) {
            if (array_key_exists($table,$baseline['tables'])) continue;
            $exists=$pdo->prepare('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=?');
            $exists->execute([$table]);
            if ((int)$exists->fetchColumn() && (int)$pdo->query('SELECT COUNT(*) FROM '.chr(96).$table.chr(96))->fetchColumn()!==0)
                throw new RuntimeException('unexpected_new_promo_data');
        }
        echo "After-deploy audit PASS: private env, media and historic row counts preserved; additive migrations verified; newly introduced promo tables contain no real codes or grants.\n";
        exit(0);
    }
    $latest = static function() use ($backupRoot): string {
        $paths = glob($backupRoot . '/snapshot-*', GLOB_ONLYDIR) ?: [];
        rsort($paths, SORT_STRING);
        if (!$paths || is_link($paths[0]) || realpath($paths[0]) !== $paths[0])
            throw new RuntimeException('no-snapshot');
        return $paths[0];
    };
    $verify = static function(string $dir, bool $verifyAudio = true) use ($shared, $walk): array {
        if (is_link($dir) || !is_file($dir . '/manifest.json') || !is_file($dir . '/database.sql')
            || !is_file($dir . '/env') || is_link($dir . '/env') || is_link($dir . '/database.sql'))
            throw new RuntimeException('snapshot-layout');
        $data = json_decode((string) file_get_contents($dir . '/manifest.json'), true, 16, JSON_THROW_ON_ERROR);
        if (!is_array($data) || ($data['format'] ?? null) !== 1 || !is_array($data['files'] ?? null)
            || !hash_equals((string) $data['env_sha256'], hash_file('sha256', $dir . '/env'))
            || !hash_equals((string) $data['sql_sha256'], hash_file('sha256', $dir . '/database.sql')))
            throw new RuntimeException('snapshot-hash');
        $audioMode = $data['audio_backup_mode'] ?? 'copied';
        if (!in_array($audioMode, ['immutable-inventory', 'copied'], true))
            throw new RuntimeException('snapshot-layout');
        if ($verifyAudio && $audioMode === 'immutable-inventory') {
            if ($walk($shared . '/audio', $shared . '/audio') !== $data['files'])
                throw new RuntimeException('snapshot-audio-hash');
        } elseif ($verifyAudio && $audioMode === 'copied') {
            foreach ($data['files'] as $name => $file) {
                $path = $dir . '/audio/' . $name;
                if ($name === '' || str_contains($name, '..') || is_link($path)
                    || !is_file($path) || filesize($path) !== $file['size']
                    || !hash_equals($file['sha256'], hash_file('sha256', $path)))
                    throw new RuntimeException('snapshot-audio-hash');
            }
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
        if (!copy($shared . '/env', $staging . '/env')) throw new RuntimeException('snapshot-env');
        chmod($staging . '/env', 0600);
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
            'user_auth_attempts', 'user_auth_events', 'user_email_security', 'entitlement_ledger', 'account_trials',
            'subscriptions', 'billing_events', 'billing_payments', 'billing_adjustments', 'referral_codes', 'referrals', 'reward_ledger', 'reward_policy', 'reward_allocations', 'service_incident_locks', 'service_incidents', 'incident_compensations', 'promo_codes', 'promo_redemptions', 'promo_attempt_buckets', 'windows_gain_variants', 'support_tickets', 'support_messages', 'admin_navigation_seen'];
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
            'audio_backup_mode'=>'immutable-inventory', 'files'=>$audio, 'tables'=>$counts];
        file_put_contents($staging . '/manifest.json',
            json_encode($manifest, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR), LOCK_EX);
        chmod($staging . '/manifest.json', 0600);
        $verify($staging);
        if (!rename($staging, $final)) throw new RuntimeException('snapshot-publish');
        echo "Stage 5 private snapshot PASS: captured SHA256 inventory of ", count($audio),
            " immutable audio objects and full SQL/config backup of ", count($tables),
            " tables; original media remains untouched.\n";
        exit(0);
    }
    $backup = $latest();
    // restore-drill verifies every original media object once. The following
    // SQL export/count operations still re-hash the SQL dump and env, but avoid
    // repeating the expensive full media inventory walk.
    $verifyAudio = !in_array($operation, ['restore-export', 'restore-counts'], true);
    $manifest = $verify($backup, $verifyAudio);
    if ($operation === 'restore-export') {
        // stdout is raw SQL, caller must redirect to private runner scratch.
        readfile($backup . '/database.sql');
        exit(0);
    }
    if ($operation === 'restore-counts') {
        // This manifest contains only table names and row counts, never row data.
        $counts = $manifest['tables'] ?? null;
        $required = ['schema_migrations', 'tracks', 'audio_assets', 'track_replacements'];
        if (!is_array($counts) || count($counts) < count($required) || count($counts) > 100)
            throw new RuntimeException('snapshot-table-counts-invalid');
        foreach ($required as $table) {
            if (!array_key_exists($table, $counts))
                throw new RuntimeException('snapshot-table-counts-incomplete');
        }
        foreach ($counts as $table => $count) {
            if (!is_string($table) || !preg_match('/^[a-z][a-z0-9_]{0,63}$/D', $table) ||
                !is_int($count) || $count < 0)
                throw new RuntimeException('snapshot-table-counts-invalid');
        }
        echo json_encode($counts, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES);
        exit(0);
    }
    if ($operation === 'restore-drill') {
        $scratch = $backupRoot . '/.drill-' . bin2hex(random_bytes(8));
        if (!mkdir($scratch, 0700)) throw new RuntimeException('drill-dir');
        if (!copy($backup . '/env', $scratch . '/env')) throw new RuntimeException('drill-env');
        chmod($scratch . '/env', 0600);
        // The release/migration path is additive and does not write existing
        // audio. Verify every original object against the captured inventory;
        // W93 separately rolls back only newly added Windows gain sidecars.
        if (!hash_equals($manifest['env_sha256'], hash_file('sha256', $scratch . '/env'))
            || $walk($shared . '/audio', $shared . '/audio') !== $manifest['files'])
            throw new RuntimeException('drill-integrity');
        $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($scratch, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
        foreach ($it as $entry) { if ($entry->isDir()) rmdir($entry->getPathname()); else unlink($entry->getPathname()); }
        rmdir($scratch);
        echo "Stage 5 restore drill PASS: config restored in isolation; all ",
            count($manifest['files']), " original audio objects match the captured SHA256 inventory.\n";
        exit(0);
    }
} catch (Throwable $e) {
    // Expose only exception class, source line and short internal error codes.
    // Never echo exception text, SQL, absolute paths, credentials, email
    // addresses or user data into public Actions logs.
    $message = $e->getMessage();
    $safeCode = preg_match('/^[a-z0-9-]{1,64}$/D', $message)
        ? $message : 'internal-exception';
    $safeClass = preg_replace('/[^A-Za-z0-9_]/', '', get_class($e));
    fwrite(STDERR, "Stage 5 operation failed safely (class=$safeClass line=" .
        $e->getLine() . " code=$safeCode). No private data logged.\n");
    exit(1);
}
