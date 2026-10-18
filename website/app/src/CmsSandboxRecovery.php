<?php
declare(strict_types=1);
namespace Celikom\Website;

use PDO;
use RuntimeException;

/**
 * CI-ONLY real MySQL + private media recovery with a durable cleanup journal.
 *
 * Deliberately NOT a production restore tool: the source MUST be the exact
 * disposable GitHub Actions database, and restored databases have a reserved
 * generated prefix. No application code, public_html or release flags change.
 *
 * A journal is fs-published BEFORE the first CREATE DATABASE. If the worker
 * crashes between DDL commits, a later cleanup under the same exclusive gate
 * removes the entire isolated recovery generation, not the source database.
 */
final class CmsSandboxRecovery
{
    private const JOURNAL = '.celikom-ci-mysql-recovery.json';
    private const FORMAT = 'celikom-ci-mysql-recovery-v1';
    private const TABLES = [
        'admin_users','media_assets','faq_categories','faq_items',
        'site_content','site_settings','content_revisions','site_state',
        'content_drafts','login_rate_limits','audit_log',
    ];

    public static function replay(
        array $config, string $manifest, string $key, string $publicDir,
        string $sandboxRoot, string $migrationFile, CmsWriteQuiescence $gate,
        ?callable $onCheckpoint = null
    ): array {
        $gate->assertExclusive();
        self::assertCi($config);
        $dir=self::privateRoot($sandboxRoot,$publicDir);
        if (file_exists($dir.'/'.self::JOURNAL) ||
            is_link($dir.'/'.self::JOURNAL)) {
            throw new RuntimeException('An unclean isolated recovery exists; call cleanup first');
        }
        // Refuse all malformed/mismatched archives BEFORE any DB DDL/media write.
        $report=CmsConsistentBackup::inspect($manifest,$key,$publicDir);
        if (($report['consistent']??false)!==true) {
            throw new RuntimeException('Recovery pair is not consistent');
        }
        $canonical=realpath(dirname(__DIR__,2).'/database/migrations/001_website_cms.sql');
        if (!is_string($canonical) || !is_file($migrationFile) ||
            is_link($migrationFile) || realpath($migrationFile)!==$canonical) {
            throw new RuntimeException('Unapproved offline CMS schema');
        }
        $sql=(string)file_get_contents($migrationFile);
        if ($sql==='' || !str_contains($sql,'CREATE TABLE IF NOT EXISTS audit_log')) {
            throw new RuntimeException('Unsupported CMS schema source');
        }
        $parts=array_filter(array_map('trim',explode(';',
            (string)preg_replace('/^--.*$/m','',$sql)
        )),static fn(string $s):bool=>$s!=='');
        if (count($parts)!==12) {
            throw new RuntimeException('CMS schema statement count changed');
        }
        $pair=json_decode((string)file_get_contents($manifest),true,32,JSON_THROW_ON_ERROR);
        $folder=realpath(dirname($manifest));
        if (!is_string($folder)) throw new RuntimeException('Recovery folder disappeared');
        $encrypted=$folder.'/'.$pair['full_db']['name'];
        $json=$folder.'/'.$pair['content_media']['name'];
        $envelope=json_decode((string)file_get_contents($json),true,512,JSON_THROW_ON_ERROR);
        $payload=$envelope['payload'];
        $assets=[];
        foreach ($payload['tables']['media_assets'] as $asset) {
            $assets[$asset['storage_key']]=$asset;
        }

        $id=bin2hex(random_bytes(8));
        $database='celikom_site_ci_replay_'.$id;
        $mediaFolder='media-'.$id;
        $record=[
            'format'=>self::FORMAT,'id'=>$id,
            'database'=>$database,'media_folder'=>$mediaFolder,
            'phase'=>'planned',
        ];
        self::writeJournal($dir,$record);
        try {
            self::checkpoint($onCheckpoint,'journal-created');
            $media=$dir.'/'.$mediaFolder;
            if (!mkdir($media,0700)) throw new RuntimeException('Cannot create isolated media tree');
            foreach ($payload['media_data'] as $stored=>$encoded) {
                if (!is_string($stored) ||
                    !preg_match('~^site-private/([a-f0-9]{40}\.(?:png|jpg|webp))$~D',$stored,$found) ||
                    !isset($assets[$stored])) {
                    throw new RuntimeException('Unexpected private recovery path');
                }
                $bytes=base64_decode($encoded,true);
                if (!is_string($bytes) || strlen($bytes)<30 ||
                    strlen($bytes)>CmsMediaStore::MAX_BYTES ||
                    !hash_equals((string)$assets[$stored]['sha256'],hash('sha256',$bytes))) {
                    throw new RuntimeException('Private recovery image digest mismatch');
                }
                $fp=fopen($media.'/'.$found[1],'xb');
                if ($fp===false) throw new RuntimeException('Cannot create staged media');
                try {
                    if (!chmod($media.'/'.$found[1],0600) ||
                        fwrite($fp,$bytes)!==strlen($bytes) || !fflush($fp)) {
                        throw new RuntimeException('Incomplete staged private media');
                    }
                } finally {
                    fclose($fp);
                }
            }
            self::checkpoint($onCheckpoint,'media-staged');

            // The only write target is a generated, brand new CI database.
            $source=Database::connect($config);
            $source->exec('CREATE DATABASE '.$database.
                ' CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');
            self::checkpoint($onCheckpoint,'database-created');
            $target=Database::connect([...$config,'dbname'=>$database]);
            foreach ($parts as $statement) $target->exec($statement);
            foreach (self::TABLES as $table) {
                $left=$source->query('SHOW COLUMNS FROM '.$table)->fetchAll(PDO::FETCH_ASSOC);
                $right=$target->query('SHOW COLUMNS FROM '.$table)->fetchAll(PDO::FETCH_ASSOC);
                if ($left!==$right || $left===[]) {
                    throw new RuntimeException('CMS migration/schema mismatch: '.$table);
                }
            }
            self::checkpoint($onCheckpoint,'schema-checked');
            // One target InnoDB transaction; the new schema's seeded state is
            // removed before importing the authenticated original state.
            $target->beginTransaction();
            try {
                $target->exec('DELETE FROM site_state WHERE id=1');
                $seen=array_fill_keys(self::TABLES,0);
                $first=true;
                CmsFullDbBackup::inspect($encrypted,$key,
                    static function(string $table,array $row) use (
                        $target,&$seen,&$first,$onCheckpoint
                    ):void {
                        if (!array_key_exists($table,$seen) || $row===[]) {
                            throw new RuntimeException('Unrecognized recovery row');
                        }
                        $columns=array_keys($row);
                        foreach ($columns as $col) {
                            if (!is_string($col) ||
                                !preg_match('/^[a-z][a-z0-9_]*$/D',$col)) {
                                throw new RuntimeException('Unsafe recovery column');
                            }
                        }
                        $stmt=$target->prepare('INSERT INTO '.$table.' ('.
                            implode(',',$columns).') VALUES ('.
                            implode(',',array_fill(0,count($columns),'?')).')');
                        $stmt->execute(array_values($row));
                        ++$seen[$table];
                        if ($first) {
                            $first=false;
                            self::checkpoint($onCheckpoint,'first-row-inserted');
                        }
                    }
                );
                foreach ($report['rows'] as $table=>$count) {
                    if (($seen[$table]??-1)!==$count) {
                        throw new RuntimeException('Recovered table count differs');
                    }
                }
                $target->commit();
            } catch (\Throwable $error) {
                if ($target->inTransaction()) $target->rollBack();
                throw $error;
            }
            self::checkpoint($onCheckpoint,'rows-committed');
            // Verify actual restored MySQL rows, not just backup metadata.
            foreach (self::TABLES as $table) {
                $count=(int)$target->query('SELECT COUNT(*) FROM '.$table)->fetchColumn();
                if ($count!==($report['rows'][$table]??-1)) {
                    throw new RuntimeException('Restored MySQL row count mismatch');
                }
            }
            foreach ($assets as $asset) {
                $bytes=CmsMediaStore::privatePreview($target,(int)$asset['id'],
                    $media,$publicDir);
                if (!hash_equals((string)$asset['sha256'],hash('sha256',$bytes['body']))) {
                    throw new RuntimeException('Staged MySQL/media mismatch');
                }
            }
            $published=$target->query('SELECT published_revision_id FROM site_state WHERE id=1')
                ->fetchColumn();
            if (($published===null?null:(int)$published)!==($report['published_id']??null)) {
                throw new RuntimeException('Recovered published revision mismatch');
            }
            self::checkpoint($onCheckpoint,'verified');
            $record['phase']='ready';
            self::writeJournal($dir,$record);
            return [
                'database'=>$database,'media_directory'=>$media,
                'rows'=>$report['rows'],'media_files'=>$report['media_files'],
                'isolated'=>true,
            ];
        } catch (\Throwable $failure) {
            try {
                self::cleanup($config,$publicDir,$sandboxRoot,$gate);
            } catch (\Throwable $cleanupError) {
                throw new RuntimeException(
                    'Isolated recovery failed; cleanup journal retained for manual CI investigation',
                    0,$failure
                );
            }
            throw $failure;
        }
    }

    /** Recover even after SIGKILL, using only a private validated CI journal. */
    public static function cleanup(
        array $config,string $publicDir,string $sandboxRoot,
        CmsWriteQuiescence $gate
    ):void {
        $gate->assertExclusive();
        self::assertCi($config);
        $dir=self::privateRoot($sandboxRoot,$publicDir);
        $journal=$dir.'/'.self::JOURNAL;
        if (!file_exists($journal) && !is_link($journal)) return;
        if (is_link($journal) || !is_file($journal) ||
            (fileperms($journal)&0077)!==0 || filesize($journal)>1024) {
            throw new RuntimeException('CI recovery journal is unsafe');
        }
        $entry=json_decode((string)file_get_contents($journal),true,16,JSON_THROW_ON_ERROR);
        if (!is_array($entry) ||
            array_keys($entry)!==['format','id','database','media_folder','phase'] ||
            $entry['format']!==self::FORMAT ||
            !is_string($entry['id']) || !preg_match('/^[a-f0-9]{16}$/D',$entry['id']) ||
            $entry['database']!=='celikom_site_ci_replay_'.$entry['id'] ||
            $entry['media_folder']!=='media-'.$entry['id'] ||
            !in_array($entry['phase'],['planned','ready'],true)) {
            throw new RuntimeException('Unrecognized CI recovery journal; no deletion performed');
        }
        $source=Database::connect($config);
        $source->exec('DROP DATABASE IF EXISTS '.$entry['database']);
        $folder=$dir.'/'.$entry['media_folder'];
        if (is_link($folder)) {
            throw new RuntimeException('Recovery media folder is a symlink');
        }
        if (is_dir($folder)) {
            foreach (scandir($folder) as $name) {
                if ($name==='.' || $name==='..') continue;
                if (!preg_match('/^[a-f0-9]{40}\.(?:png|jpg|webp)$/D',$name) ||
                    is_link($folder.'/'.$name) || !is_file($folder.'/'.$name)) {
                    throw new RuntimeException('Unexpected media in CI recovery directory');
                }
                if (!unlink($folder.'/'.$name)) throw new RuntimeException('Cannot clear staged image');
            }
            if (!rmdir($folder)) throw new RuntimeException('Cannot clear staged image folder');
        }
        if (!unlink($journal)) throw new RuntimeException('Cannot clear CI recovery journal');
    }

    private static function assertCi(array $config):void
    {
        if (getenv('CI')!=='true' ||
            getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
            ($config['host']??null)!=='127.0.0.1' ||
            ($config['dbname']??null)!=='celikom_site_test') {
            throw new RuntimeException('MySQL recovery is ONLY permitted in disposable CI');
        }
    }

    private static function privateRoot(string $root,string $publicDir):string
    {
        $path=realpath($root);
        $public=realpath($publicDir);
        if (!is_string($path) || !is_string($public) || !is_dir($path) ||
            !is_dir($public) || is_link($root) ||
            $path===$public || str_starts_with($path,$public.'/') ||
            str_starts_with($public,$path.'/') ||
            (fileperms($path)&0077)!==0) {
            throw new RuntimeException('CI recovery must use an isolated private root');
        }
        return $path;
    }

    private static function writeJournal(string $dir,array $record):void
    {
        $temp=$dir.'/.celikom-ci-recovery-'.bin2hex(random_bytes(8)).'.tmp';
        $handle=fopen($temp,'xb');
        if ($handle===false) throw new RuntimeException('Cannot allocate recovery journal');
        try {
            $json=json_encode($record,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES);
            if (!chmod($temp,0600) ||
                fwrite($handle,$json)!==strlen($json) || !fflush($handle)) {
                throw new RuntimeException('Cannot persist recovery journal');
            }
        } finally {
            fclose($handle);
        }
        if (!rename($temp,$dir.'/'.self::JOURNAL)) {
            @unlink($temp);
            throw new RuntimeException('Cannot publish recovery journal');
        }
    }

    private static function checkpoint(?callable $callback,string $stage):void
    {
        if ($callback!==null) $callback($stage);
    }
}
