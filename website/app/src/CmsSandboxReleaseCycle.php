<?php
declare(strict_types=1);
namespace Celikom\Website;

use RuntimeException;

/**
 * Offline-only CI release intent, NOT a production deployer.
 *
 * An exclusive CMS write lease guards each state change. The journal is
 * published before changing the atomic private generation pointer.
 * Unconfirmed or crashed switches can be reconciled to the prior generation
 * by an independent worker; no destructive reverse MySQL DDL is performed.
 * Neither journal nor pointer is consulted by live website entrypoints.
 */
final class CmsSandboxReleaseCycle
{
    private const NAME='.celikom-ci-release-cycle.json';
    private const FORMAT='celikom-ci-release-cycle-v1';

    /** Start a new baseline -> independently validated candidate transition. */
    public static function prepare(
        array $config,string $root,string $public,string $candidate,
        CmsWriteQuiescence $lease
    ):array {
        $dir=self::directory($config,$root,$public,$lease);
        $path=$dir.'/'.self::NAME;
        if (file_exists($path) || is_link($path)) {
            throw new RuntimeException('Existing release intent must be resolved first');
        }
        $active=CmsSandboxGeneration::active($config,$dir,$public,$lease)['record'];
        if ($active['generation']!=='gen-baseline' ||
            !preg_match('/^gen-[a-f0-9]{16}$/D',$candidate)) {
            throw new RuntimeException('Only baseline to isolated candidate is allowed');
        }
        $healthy=CmsSandboxGeneration::inspectCandidate(
            $config,$dir,$public,$candidate,$lease
        );
        if ($healthy['health']['healthy']!==true) {
            throw new RuntimeException('Unhealthy staged generation');
        }
        $entry=['format'=>self::FORMAT,'id'=>bin2hex(random_bytes(12)),
            'previous'=>'gen-baseline','candidate'=>$candidate,
            'phase'=>'prepared'];
        self::persist($path,$entry,false);
        return ['phase'=>'prepared','id'=>$entry['id']];
    }

    /** Switch pointer, then persist journal phase. Failures are reconciled. */
    public static function activate(
        array $config,string $root,string $public,CmsWriteQuiescence $lease,
        ?callable $checkpoint=null
    ):array {
        $dir=self::directory($config,$root,$public,$lease);
        $path=$dir.'/'.self::NAME;
        $entry=self::load($path);
        if ($entry['phase']!=='prepared') {
            throw new RuntimeException('Release intent is not prepared');
        }
        $active=CmsSandboxGeneration::active($config,$dir,$public,$lease);
        if ($active['record']['generation']!==$entry['previous']) {
            throw new RuntimeException('Stale release intent cannot activate');
        }
        if ($checkpoint!==null) $checkpoint('before-pointer-rename');
        CmsSandboxGeneration::select(
            $config,$dir,$public,$entry['candidate'],$lease
        );
        if ($checkpoint!==null) $checkpoint('after-pointer-rename');
        $entry['phase']='activated';
        self::persist($path,$entry,true);
        if ($checkpoint!==null) $checkpoint('after-journal-commit');
        return ['phase'=>'activated','generation'=>$entry['candidate']];
    }

    /** Only explicitly verified healthy active generation can be confirmed. */
    public static function confirm(
        array $config,string $root,string $public,CmsWriteQuiescence $lease
    ):array {
        $dir=self::directory($config,$root,$public,$lease);
        $path=$dir.'/'.self::NAME;
        $entry=self::load($path);
        if ($entry['phase']!=='activated') {
            throw new RuntimeException('Cannot confirm incomplete switch');
        }
        $active=CmsSandboxGeneration::active($config,$dir,$public,$lease);
        if ($active['record']['generation']!==$entry['candidate'] ||
            $active['health']['healthy']!==true) {
            throw new RuntimeException('Candidate is not current and healthy');
        }
        self::finish($path);
        return ['confirmed'=>true,'generation'=>$entry['candidate']];
    }

    /**
     * On restart, an unconfirmed transition is rolled back. The old MySQL and
     * media must still pass health before a pointer is changed.
     * The candidate DB is retained until explicit safe cleanup.
     */
    public static function reconcile(
        array $config,string $root,string $public,CmsWriteQuiescence $lease
    ):array {
        $dir=self::directory($config,$root,$public,$lease);
        $path=$dir.'/'.self::NAME;
        $entry=self::load($path);
        $active=CmsSandboxGeneration::active($config,$dir,$public,$lease);
        $name=$active['record']['generation'];
        if ($name===$entry['candidate']) {
            CmsSandboxGeneration::select(
                $config,$dir,$public,$entry['previous'],$lease
            );
        } elseif ($name!==$entry['previous']) {
            throw new RuntimeException('Release pointer diverged; manual CI investigation');
        }
        $previous=CmsSandboxGeneration::active($config,$dir,$public,$lease);
        if ($previous['record']['generation']!==$entry['previous'] ||
            $previous['health']['healthy']!==true) {
            throw new RuntimeException('Recovery generation failed health');
        }
        self::finish($path);
        return ['reconciled'=>true,'generation'=>$entry['previous'],
            'candidate'=>$entry['candidate']];
    }

    private static function directory(
        array $config,string $root,string $public,CmsWriteQuiescence $lease
    ):string {
        // This class cannot be used to switch a real server/database.
        $lease->assertExclusive();
        if (getenv('CI')!=='true' ||
            getenv('CELIKOM_SITE_SANDBOX_RESTORE')!=='1' ||
            ($config['host']??null)!=='127.0.0.1' ||
            ($config['dbname']??null)!=='celikom_site_test') {
            throw new RuntimeException('Release journal can only run in disposable CI');
        }
        $dir=realpath($root);
        $web=realpath($public);
        if (!is_string($dir) || !is_string($web) || is_link($root) ||
            !is_dir($dir) || !is_dir($web) || $dir===$web ||
            str_starts_with($dir,$web.'/') || str_starts_with($web,$dir.'/') ||
            (fileperms($dir)&0077)!==0) {
            throw new RuntimeException('Release journal requires private test root');
        }
        return $dir;
    }

    private static function validate(array $record):void
    {
        if (array_keys($record)!==['format','id','previous','candidate','phase'] ||
            ($record['format']??null)!==self::FORMAT ||
            !is_string($record['id']??null) ||
            !preg_match('/^[a-f0-9]{24}$/D',$record['id']) ||
            $record['previous']!=='gen-baseline' ||
            !is_string($record['candidate']) ||
            !preg_match('/^gen-[a-f0-9]{16}$/D',$record['candidate']) ||
            !in_array($record['phase'],['prepared','activated'],true)) {
            throw new RuntimeException('Invalid release recovery journal');
        }
    }

    private static function load(string $path):array
    {
        clearstatcache(true,$path);
        if (is_link($path) || !is_file($path) ||
            filesize($path)<100 || filesize($path)>512 ||
            (fileperms($path)&0077)!==0) {
            throw new RuntimeException('Missing or unsafe release intent journal');
        }
        $entry=json_decode((string)file_get_contents($path),true,16,JSON_THROW_ON_ERROR);
        if (!is_array($entry)) throw new RuntimeException('Invalid journal body');
        self::validate($entry);
        return $entry;
    }

    private static function persist(string $path,array $record,bool $replace):void
    {
        self::validate($record);
        if (is_link($path) || (!$replace && file_exists($path))) {
            throw new RuntimeException('Unsafe existing release intent');
        }
        $tmp=dirname($path).'/.celikom-ci-release-'.bin2hex(random_bytes(8)).'.tmp';
        $fp=fopen($tmp,'xb');
        if ($fp===false) throw new RuntimeException('Cannot allocate release journal');
        try {
            $bytes=json_encode($record,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES);
            if (!chmod($tmp,0600) ||
                fwrite($fp,$bytes)!==strlen($bytes) || !fflush($fp)) {
                throw new RuntimeException('Release journal is incomplete');
            }
        } catch (\Throwable $error) {
            fclose($fp);
            @unlink($tmp);
            throw $error;
        }
        fclose($fp);
        if (!rename($tmp,$path)) {
            @unlink($tmp);
            throw new RuntimeException('Cannot publish release journal');
        }
    }

    private static function finish(string $path):void
    {
        if (is_link($path) || !is_file($path) || !unlink($path)) {
            throw new RuntimeException('Cannot clear resolved release journal');
        }
    }
}
