<?php
declare(strict_types=1);
namespace Celikom\Website;

use PDO;
use RuntimeException;

/**
 * Stage 10: one MySQL/InnoDB repeatable-read snapshot for BOTH exports.
 *
 * Content JSON includes private image bytes; full DB backup is authenticated
 * and encrypted. Only the manifest completes a restore point. Partial files
 * from a failed capture are removed. No DB restore, deployment, or release
 * approval is performed here.
 *
 * IMPORTANT: This guarantees a single *database* snapshot, not filesystem
 * atomicity with mutable media. The image exporter validates stored digests;
 * production needs a write/GC freeze and a protected offsite encrypted copy
 * of the plaintext content snapshot before using this procedure.
 */
final class CmsConsistentBackup
{
    private const FORMAT = 'celikom-site-consistent-restore-v1';

    /** @return array{manifest:string,report:array} */
    public static function capture(
        PDO $pdo, string $bundleDirectory, string $mediaDirectory,
        string $publicDirectory, string $key
    ): array {
        $dir = self::safeBundleDir($bundleDirectory, $publicDirectory);
        if ($pdo->inTransaction()) {
            throw new RuntimeException('Capture must own an independent database transaction');
        }
        $full = null;
        $content = null;
        $manifest = null;
        $temp = null;
        try {
            $pdo->exec('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
            $pdo->beginTransaction();
            // Establish a common InnoDB consistent read view BEFORE either
            // exporter starts, even if another connection later edits drafts.
            $pdo->query('SELECT id FROM site_state WHERE id=1')->fetchAll(PDO::FETCH_ASSOC);
            $full = CmsFullDbBackup::export(
                $pdo, $dir, $publicDirectory, $key, true
            );
            $content = CmsBackup::export(
                $pdo, $dir, $mediaDirectory, $publicDirectory, true
            );
            $report = CmsRecoveryPair::inspect(
                $full, $content, $key, $publicDirectory
            );
            if (($report['consistent'] ?? false) !== true) {
                throw new RuntimeException('Joint recovery check failed');
            }
            $pdo->commit();

            $id = gmdate('Ymd-His').'-'.bin2hex(random_bytes(12));
            $manifest = $dir.'/celikom-restore-point-'.$id.'.json';
            $temp = $dir.'/.celikom-restore-point-'.$id.'.tmp';
            $payload = [
                'format' => self::FORMAT,
                'created_utc' => gmdate('Y-m-d\TH:i:s\Z'),
                'full_db' => ['name' => basename($full), 'sha256' => hash_file('sha256', $full)],
                'content_media' => ['name' => basename($content), 'sha256' => hash_file('sha256', $content)],
            ];
            $encoded = json_encode(
                $payload, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES
            );
            $fp = fopen($temp, 'xb');
            if ($fp === false) throw new RuntimeException('Cannot allocate restore manifest');
            try {
                if (!chmod($temp, 0600) ||
                    fwrite($fp, $encoded) !== strlen($encoded) ||
                    !fflush($fp)) {
                    throw new RuntimeException('Cannot securely write restore manifest');
                }
            } finally {
                fclose($fp);
            }
            if (!rename($temp, $manifest)) {
                throw new RuntimeException('Cannot atomically publish restore manifest');
            }
            $temp = null;
            $verified = self::inspect($manifest, $key, $publicDirectory);
            return ['manifest' => $manifest, 'report' => $verified];
        } catch (\Throwable $error) {
            if ($pdo->inTransaction()) $pdo->rollBack();
            foreach ([$temp, $manifest, $content, $full] as $file) {
                if (is_string($file) && is_file($file) && !is_link($file)) {
                    @unlink($file);
                }
            }
            throw $error;
        }
    }

    /** Recheck all files, digests, encrypted DB, image bytes and row equality. */
    public static function inspect(
        string $manifest, string $key, string $publicDirectory
    ): array {
        clearstatcache(true, $manifest);
        $public = realpath($publicDirectory);
        if (!is_string($public) || is_link($manifest) ||
            !is_file($manifest) || (fileperms($manifest) & 0077) !== 0 ||
            filesize($manifest) > 4096 || filesize($manifest) < 100) {
            throw new RuntimeException('Restore manifest must be a private regular file');
        }
        $dir = self::safeBundleDir(dirname($manifest), $publicDirectory);
        $resolved = realpath($manifest);
        if (!is_string($resolved) || dirname($resolved) !== $dir) {
            throw new RuntimeException('Restore manifest escaped its private directory');
        }
        $json = json_decode((string)file_get_contents($manifest), true, 32, JSON_THROW_ON_ERROR);
        if (!is_array($json) || array_keys($json) !==
            ['format', 'created_utc', 'full_db', 'content_media'] ||
            $json['format'] !== self::FORMAT) {
            throw new RuntimeException('Unknown coordinated restore format');
        }
        $paths = [];
        foreach (['full_db', 'content_media'] as $kind) {
            $entry = $json[$kind];
            if (!is_array($entry) || array_keys($entry) !== ['name', 'sha256'] ||
                !is_string($entry['name']) ||
                !preg_match('/^celikom-[a-z0-9-]{12,100}\.(?:json|sbox)$/D', $entry['name']) ||
                !is_string($entry['sha256']) ||
                !preg_match('/^[a-f0-9]{64}$/D', $entry['sha256'])) {
                throw new RuntimeException('Invalid restore artifact reference');
            }
            $path = $dir.'/'.$entry['name'];
            if (!is_file($path) || is_link($path) ||
                realpath($path) !== $path ||
                (fileperms($path) & 0077) !== 0 ||
                !hash_equals($entry['sha256'], (string)hash_file('sha256', $path))) {
                throw new RuntimeException('Restore artifact missing, exposed or modified');
            }
            $paths[$kind] = $path;
        }
        if ($paths['full_db'] === $paths['content_media'] ||
            !str_ends_with($paths['full_db'], '.sbox') ||
            !str_ends_with($paths['content_media'], '.json')) {
            throw new RuntimeException('Invalid restore artifact pairing');
        }
        return CmsRecoveryPair::inspect(
            $paths['full_db'], $paths['content_media'], $key, $publicDirectory
        );
    }

    private static function safeBundleDir(
        string $directory, string $publicDirectory
    ): string {
        $dir = realpath($directory);
        $public = realpath($publicDirectory);
        if (!is_string($dir) || !is_string($public) ||
            !is_dir($dir) || !is_dir($public) ||
            is_link($directory) ||
            $dir === $public ||
            str_starts_with($dir, $public.'/') ||
            str_starts_with($public, $dir.'/') ||
            (fileperms($dir) & 0077) !== 0) {
            throw new RuntimeException('Restore point must use an owner-only private folder');
        }
        return $dir;
    }
}
