<?php
declare(strict_types=1);
namespace Celikom\Website;

use PDO;
use RuntimeException;

/**
 * Stage 10 ONLY: immutable offline generation selection against disposable CI.
 * The pointer is private test metadata, NEVER consulted by live HTTP routes.
 * Two isolated MySQL generations coexist; rollback changes ONE private pointer,
 * never runs a backwards SQL migration over a newer DB.
 */
final class CmsSandboxGeneration
{
    private const ACTIVE = '.celikom-ci-active-generation.json';
    private const FORMAT = 'celikom-ci-generation-pointer-v1';
    private const MIGRATION = '002_ci_generation_only.sql';

    private static function guard(array $config, string $root, string $public, CmsWriteQuiescence $lease): string
    {
        $lease->assertExclusive();
        if (getenv('CI') !== 'true' ||
            getenv('CELIKOM_SITE_SANDBOX_RESTORE') !== '1' ||
            ($config['host'] ?? null) !== '127.0.0.1' ||
            ($config['dbname'] ?? null) !== 'celikom_site_test') {
            throw new RuntimeException('Offline generation operation restricted to disposable CI');
        }
        $dir = realpath($root);
        $web = realpath($public);
        if (!is_string($dir) || !is_string($web) || is_link($root) ||
            !is_dir($dir) || !is_dir($web) ||
            $dir === $web || str_starts_with($dir, $web.'/') ||
            str_starts_with($web, $dir.'/') ||
            (fileperms($dir) & 0077) !== 0) {
            throw new RuntimeException('Release simulation must use isolated private directory');
        }
        return $dir;
    }

    private static function validRecord(array $value): void
    {
        if (array_keys($value) !== ['format','generation','database','schema_version'] ||
            ($value['format'] ?? null) !== self::FORMAT ||
            !is_string($value['generation']) ||
            !preg_match('/^gen-(?:baseline|[a-f0-9]{16})$/D', $value['generation']) ||
            !is_string($value['database']) ||
            !in_array($value['schema_version'], [1, 2], true)) {
            throw new RuntimeException('Invalid offline release pointer');
        }
        if ($value['generation'] === 'gen-baseline') {
            if ($value['database'] !== 'celikom_site_test' || $value['schema_version'] !== 1) {
                throw new RuntimeException('Baseline pointer attempted to select another database');
            }
        } else {
            if ($value['database'] !== 'celikom_site_ci_replay_'.
                substr($value['generation'], 4) || $value['schema_version'] !== 2) {
                throw new RuntimeException('Candidate pointer has incorrect database binding');
            }
        }
    }

    /** Private immutable generation metadata, not a public_html symlink. */
    private static function writeRecord(string $path, array $value, bool $overwrite): void
    {
        self::validRecord($value);
        if (is_link($path) || (!$overwrite && file_exists($path))) {
            throw new RuntimeException('Refusing overwrite of generation state');
        }
        $tmp=dirname($path).'/.celikom-ci-gen-'.bin2hex(random_bytes(10)).'.tmp';
        $fp=fopen($tmp, 'xb');
        if ($fp===false) throw new RuntimeException('Cannot allocate release state');
        try {
            $raw=json_encode($value, JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES);
            if (!chmod($tmp, 0600) || fwrite($fp, $raw) !== strlen($raw) || !fflush($fp)) {
                throw new RuntimeException('Cannot persist release state');
            }
        } catch (\\Throwable $error) {
            fclose($fp);
            @unlink($tmp);
            throw $error;
        }
        fclose($fp);
        if (!rename($tmp, $path)) {
            @unlink($tmp);
            throw new RuntimeException('Cannot atomically commit release state');
        }
    }

    private static function readRecord(string $path): array
    {
        clearstatcache(true, $path);
        if (is_link($path) || !is_file($path) || filesize($path) > 512 ||
            filesize($path) < 75 || (fileperms($path) & 0077) !== 0) {
            throw new RuntimeException('Offline generation state is missing or unsafe');
        }
        $record=json_decode((string)file_get_contents($path),true,16,JSON_THROW_ON_ERROR);
        if (!is_array($record)) throw new RuntimeException('Invalid release state envelope');
        self::validRecord($record);
        return $record;
    }

    private static function generation(string $root, string $name): array
    {
        $marker=$root.'/'.$name.'/.generation.json';
        $record=self::readRecord($marker);
        if ($record['generation'] !== $name) {
            throw new RuntimeException('Staged generation identity mismatch');
        }
        $folder=realpath($root.'/'.$name);
        $media=realpath($root.'/'.$name.'/media');
        if (!is_string($folder) || $folder !== $root.'/'.$name ||
            !is_string($media) || $media !== $folder.'/media' ||
            is_link($root.'/'.$name) || is_link($root.'/'.$name.'/media') ||
            (fileperms($folder)&0077)!==0 || (fileperms($media)&0077)!==0) {
            throw new RuntimeException('Generation media tree is not isolated');
        }
        return [$record, $media];
    }

    /** Re-validate actual SQL and every private image before promotion/rollback. */
    private static function health(array $config, string $root, string $public, array $record): array
    {
        self::validRecord($record);
        [$saved, $media]=self::generation($root,$record['generation']);
        if ($saved !== $record) throw new RuntimeException('Release generation metadata drift');
        $pdo=Database::connect([...$config,'dbname'=>$record['database']]);
        $state=$pdo->query('SELECT COUNT(*) FROM site_state WHERE id=1')->fetchColumn();
        $owners=(int)$pdo->query('SELECT COUNT(*) FROM admin_users')->fetchColumn();
        if ((int)$state !== 1 || $owners<1) {
            throw new RuntimeException('Generation lost CMS state or owner');
        }
        $hasColumn=$pdo->query(
            "SELECT COUNT(*) FROM information_schema.COLUMNS ".
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='site_settings' ".
            "AND COLUMN_NAME='release_generation'"
        )->fetchColumn();
        if ($record['schema_version']===2) {
            if ((int)$hasColumn !== 1 ||
                (int)$pdo->query('SELECT COUNT(*) FROM cms_schema_versions '.
                    'WHERE version=2 AND migration_name='.
                    "'ci-offline-generation-v2'")->fetchColumn() !== 1) {
                throw new RuntimeException('Version 2 MySQL schema is incomplete');
            }
        } elseif ((int)$hasColumn !== 0) {
            throw new RuntimeException('Version 1 schema unexpectedly changed');
        }
        $q=$pdo->query('SELECT id FROM media_assets ORDER BY id');
        $count=0;
        while (($id=$q->fetchColumn())!==false) {
            CmsMediaStore::privatePreview($pdo,(int)$id,$media,$public);
            ++$count;
        }
        $expectedFiles=(int)$pdo->query('SELECT COUNT(*) FROM media_assets')->fetchColumn();
        if ($count!==$expectedFiles) throw new RuntimeException('CMS media inventory mismatch');
        $files=scandir($media);
        if (!is_array($files)) throw new RuntimeException('Cannot scan generation media');
        $stored=array_values(array_diff($files,['.','..']));
        if (count($stored)!==$count) throw new RuntimeException('Stale or unexpected media files');
        return ['healthy'=>true,'schema_version'=>$record['schema_version'],
            'database'=>$record['database'],'media_files'=>$count];
    }

    /** Establish a baseline from actual disposable CMS database and private files. */
    public static function seed(
        array $config, string $root, string $public, string $baselineMedia,
        CmsWriteQuiescence $lease
    ): array {
        $dir=self::guard($config,$root,$public,$lease);
        if (file_exists($dir.'/'.self::ACTIVE) || is_dir($dir.'/gen-baseline')) {
            throw new RuntimeException('Baseline already staged');
        }
        $source=realpath($baselineMedia);
        if (!is_string($source) || !is_dir($source) || is_link($baselineMedia) ||
            $source===$dir || str_starts_with($source,$dir.'/') ||
            $source===realpath($public) || str_starts_with($source,realpath($public).'/')) {
            throw new RuntimeException('Invalid source media');
        }
        $record=['format'=>self::FORMAT,'generation'=>'gen-baseline',
            'database'=>'celikom_site_test','schema_version'=>1];
        self::stageFiles($config,$dir,$public,$record,$source);
        try {
            $result=self::health($config,$dir,$public,$record);
            self::writeRecord($dir.'/'.self::ACTIVE,$record,false);
            return $result;
        } catch (\\Throwable $error) {
            self::deleteStage($dir,$record['generation']);
            throw $error;
        }
    }

    /** Copy bytes into an isolated immutable folder, verify against SQL. */
    private static function stageFiles(
        array $config,string $dir,string $public,array $record,string $source
    ):void {
        $folder=$dir.'/'.$record['generation'];
        if (!mkdir($folder,0700)) throw new RuntimeException('Generation already exists');
        try {
            if (!mkdir($folder.'/media',0700)) throw new RuntimeException('Media stage unavailable');
            $db=Database::connect([...$config,'dbname'=>$record['database']]);
            $stmt=$db->query('SELECT id,storage_key FROM media_assets ORDER BY id');
            while (($row=$stmt->fetch(PDO::FETCH_ASSOC))!==false) {
                $storage=(string)$row['storage_key'];
                if (!preg_match('~^site-private/([a-f0-9]{40}\.(?:png|jpg|webp))$~D',
                    $storage,$found)) throw new RuntimeException('Invalid staged media key');
                $checked=CmsMediaStore::privatePreview($db,(int)$row['id'],$source,$public);
                $path=$folder.'/media/'.$found[1];
                $fp=fopen($path,'xb');
                if ($fp===false) throw new RuntimeException('Cannot allocate staged media');
                try {
                    if (!chmod($path,0600) ||
                        fwrite($fp,$checked['body'])!==strlen($checked['body']) ||
                        !fflush($fp)) throw new RuntimeException('Failed staged media write');
                } finally { fclose($fp); }
            }
            self::writeRecord($folder.'/.generation.json',$record,false);
        } catch (\Throwable $e) {
            self::deleteStage($dir,$record['generation']);
            throw $e;
        }
    }

    /**
     * Version 1 -> 2 migration of a disposable restored generation only.
     * A failed MySQL DDL sequence is NOT rolled back in-place: caller must
     * discard that candidate via CmsSandboxRecovery::cleanup and retry.
     */
    public static function migrateAndStage(
        array $config,string $root,string $public,array $recovery,
        string $migrationFile,CmsWriteQuiescence $lease,
        ?callable $checkpoint=null
    ):array {
        $dir=self::guard($config,$root,$public,$lease);
        $baseline=self::readRecord($dir.'/'.self::ACTIVE);
        if ($baseline['generation']!=='gen-baseline' || $baseline['schema_version']!==1) {
            throw new RuntimeException('Migration requires unchanged baseline selection');
        }
        $dbName=$recovery['database']??null;
        $sourceMedia=$recovery['media_directory']??null;
        if (!is_string($dbName) ||
            !preg_match('/^celikom_site_ci_replay_([a-f0-9]{16})$/D',$dbName,$found) ||
            !is_string($sourceMedia) || !is_dir($sourceMedia) || is_link($sourceMedia) ||
            !isset($recovery['isolated']) || $recovery['isolated']!==true) {
            throw new RuntimeException('Invalid disposable recovery generation');
        }
        $record=['format'=>self::FORMAT,'generation'=>'gen-'.$found[1],
            'database'=>$dbName,'schema_version'=>2];
        $canonical=realpath(dirname(__DIR__,2).'/tests/fixtures/'.self::MIGRATION);
        if (!is_string($canonical) || is_link($migrationFile) ||
            realpath($migrationFile)!==$canonical) {
            throw new RuntimeException('Only CI migration 002 is authorized');
        }
        $sql=(string)file_get_contents($canonical);
        $commands=array_values(array_filter(array_map('trim',explode(';',
            (string)preg_replace('/^--.*$/m','',$sql)
        )),static fn(string $x):bool=>$x!==''));
        // No freeform SQL from environment, users or arbitrary migration files.
        if (count($commands)!==3 ||
            $commands[0] !== "CREATE TABLE cms_schema_versions (\n".
                "  version INT UNSIGNED NOT NULL PRIMARY KEY,\n".
                "  migration_name VARCHAR(80) NOT NULL\n".
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci" ||
            $commands[1] !== "ALTER TABLE site_settings ADD COLUMN release_generation VARCHAR(16) NOT NULL DEFAULT 'v2'" ||
            $commands[2] !== "INSERT INTO cms_schema_versions(version,migration_name) VALUES(2,'ci-offline-generation-v2')") {
            throw new RuntimeException('Unsupported versioned SQL migration');
        }
        $db=Database::connect([...$config,'dbname'=>$dbName]);
        $exists=$db->query("SELECT COUNT(*) FROM information_schema.TABLES ".
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='cms_schema_versions'")->fetchColumn();
        if ((int)$exists!==0) throw new RuntimeException('Migration already or partly applied');
        self::stageFiles($config,$dir,$public,$record,$sourceMedia);
        try {
            if ($checkpoint!==null) $checkpoint('media-staged');
            foreach ($commands as $index=>$command) {
                $db->exec($command);
                if ($checkpoint!==null) $checkpoint('migration-step-'.($index+1));
            }
            $health=self::health($config,$dir,$public,$record);
            if ($checkpoint!==null) $checkpoint('candidate-healthy');
            return ['generation'=>$record['generation'],'database'=>$dbName,
                'health'=>$health,'isolated'=>true];
        } catch (\Throwable $e) {
            self::deleteStage($dir,$record['generation']);
            throw $e;
        }
    }

    public static function active(
        array $config,string $root,string $public,CmsWriteQuiescence $lease
    ):array {
        $dir=self::guard($config,$root,$public,$lease);
        $record=self::readRecord($dir.'/'.self::ACTIVE);
        return ['record'=>$record,'health'=>self::health($config,$dir,$public,$record)];
    }

    /** Atomic offline selector: when interrupted, either old or new pointer survives. */
    public static function select(
        array $config,string $root,string $public,string $generation,
        CmsWriteQuiescence $lease,?callable $checkpoint=null
    ):array {
        $dir=self::guard($config,$root,$public,$lease);
        $old=self::readRecord($dir.'/'.self::ACTIVE);
        [$candidate]=self::generation($dir,$generation);
        $health=self::health($config,$dir,$public,$candidate);
        if ($checkpoint!==null) $checkpoint('before-switch');
        self::writeRecord($dir.'/'.self::ACTIVE,$candidate,true);
        if ($checkpoint!==null) $checkpoint('after-switch');
        return ['previous'=>$old,'active'=>$candidate,'health'=>$health];
    }

    /** Fail-closed cleanup of any abandoned unselected candidate files. */
    public static function discard(
        array $config,string $root,string $public,string $generation,
        CmsWriteQuiescence $lease
    ):void {
        $dir=self::guard($config,$root,$public,$lease);
        $active=self::readRecord($dir.'/'.self::ACTIVE);
        if ($generation===$active['generation'] ||
            !preg_match('/^gen-[a-f0-9]{16}$/D',$generation)) {
            throw new RuntimeException('Never delete active or baseline generation');
        }
        self::deleteStage($dir,$generation);
    }

    private static function deleteStage(string $dir,string $name):void
    {
        if (!preg_match('/^gen-(?:baseline|[a-f0-9]{16})$/D',$name)) {
            throw new RuntimeException('Unexpected generation cleanup target');
        }
        $folder=$dir.'/'.$name;
        if (is_link($folder)) throw new RuntimeException('Refusing symlink stage cleanup');
        if (!is_dir($folder)) return;
        $media=$folder.'/media';
        if (is_link($media)) throw new RuntimeException('Unsafe media cleanup target');
        if (is_dir($media)) {
            foreach (scandir($media) as $file) {
                if ($file==='.' || $file==='..') continue;
                if (!preg_match('/^[a-f0-9]{40}\.(?:png|jpg|webp)$/D',$file) ||
                    is_link($media.'/'.$file) || !is_file($media.'/'.$file)) {
                    throw new RuntimeException('Foreign file in staged generation');
                }
                if (!unlink($media.'/'.$file)) throw new RuntimeException('Cannot remove staged image');
            }
            rmdir($media);
        }
        $meta=$folder.'/.generation.json';
        if (is_link($meta)) throw new RuntimeException('Unsafe staged metadata');
        if (is_file($meta)) unlink($meta);
        if (scandir($folder)!==['.','..']) throw new RuntimeException('Foreign staged file');
        rmdir($folder);
    }
}
