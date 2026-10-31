<?php
declare(strict_types=1);
namespace Celikom\Website;

use PDO;
use RuntimeException;

/**
 * CLI-only consistent backup of CMS CONTENT and its private images.
 * DOES NOT export password hashes, admin accounts, sessions or audit logs:
 * this is not a database disaster-recovery dump. Restore remains deliberately
 * offline/manual until separately reviewed. No public routes consume backups.
 */
final class CmsBackup
{
    public static function export(
        PDO $pdo,string $backupDirectory,string $mediaDirectory,string $publicDirectory,
        bool $existingSnapshot=false
    ): string {
        $output=realpath($backupDirectory);
        $storage=realpath($mediaDirectory);
        $public=realpath($publicDirectory);
        if($output===false || $storage===false || $public===false ||
            !is_dir($output) || !is_dir($storage) || !is_dir($public) ||
            !self::privatePath($output,$public) ||
            !self::privatePath($storage,$public) ||
            $output===$storage) {
            throw new RuntimeException('CMS backup requires separate private directories');
        }
        if ($existingSnapshot) {
            if (!$pdo->inTransaction()) {
                throw new RuntimeException('An active caller-owned DB snapshot is required');
            }
        } else {
            $pdo->exec('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
            $pdo->beginTransaction();
        }
        try {
            $snapshot=[];
            foreach([
                'content_drafts'=>'SELECT id,draft_json,optimistic_version,updated_at FROM content_drafts ORDER BY id',
                'site_state'=>'SELECT id,published_revision_id,updated_at FROM site_state ORDER BY id',
                'content_revisions'=>'SELECT id,snapshot_json,change_note,created_at FROM content_revisions ORDER BY id',
                'media_assets'=>'SELECT id,storage_key,original_filename,mime_type,sha256,pixel_width,pixel_height,alt_text,created_at,is_active FROM media_assets ORDER BY id',
            ] as $table=>$query) {
                $snapshot[$table]=$pdo->query($query)->fetchAll(PDO::FETCH_ASSOC);
            }
            if(count($snapshot['site_state'])!==1 ||
                (int)$snapshot['site_state'][0]['id']!==1 ||
                count($snapshot['content_drafts'])>1 ||
                count($snapshot['media_assets'])>100 ||
                count($snapshot['content_revisions'])>5000) {
                throw new RuntimeException('Content backup state exceeds verified limits');
            }
            $files=[];
            $total=0;
            foreach($snapshot['media_assets'] as $asset) {
                $key=(string)$asset['storage_key'];
                if(!preg_match('~^site-private/([a-f0-9]{40}\.(?:png|jpg|webp))$~D',$key,$match)) {
                    throw new RuntimeException('Unexpected media storage reference');
                }
                $path=$storage.'/'.$match[1];
                if(!is_file($path) || is_link($path) || !is_readable($path)) {
                    throw new RuntimeException('Private media file is missing');
                }
                $size=filesize($path);
                if(!is_int($size) || $size<30 || $size>CmsMediaStore::MAX_BYTES ||
                    $total+$size>25_165_824) {
                    throw new RuntimeException('Private media size limit exceeded');
                }
                $bytes=file_get_contents($path);
                if(!is_string($bytes) || strlen($bytes)!==$size ||
                    !hash_equals((string)$asset['sha256'],hash('sha256',$bytes))) {
                    throw new RuntimeException('Private media integrity mismatch');
                }
                $files[$key]=base64_encode($bytes);
                $total+=$size;
            }
            if (!$existingSnapshot) $pdo->commit();
            $snapshot=['format'=>'celikom-site-content-backup-v1',
                'exported_utc'=>gmdate('Y-m-d\TH:i:s\Z'),
                'tables'=>$snapshot,'media_data'=>$files];
            $canonical=json_encode($snapshot,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
            $envelope=json_encode([
                'sha256'=>hash('sha256',$canonical),
                'payload'=>$snapshot,
            ],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
            if(strlen($envelope)>35_000_000)throw new RuntimeException('Backup exceeds size limit');
            $name='celikom-site-content-'.gmdate('Ymd-His').'-'.bin2hex(random_bytes(6)).'.json';
            $tmp=$output.'/.'.$name.'.tmp';
            $target=$output.'/'.$name;
            $handle=fopen($tmp,'x+b');
            if($handle===false)throw new RuntimeException('Cannot create private backup');
            try {
                if(!chmod($tmp,0600) ||
                    fwrite($handle,$envelope)!==strlen($envelope) ||
                    !fflush($handle)) {
                    throw new RuntimeException('Backup write failed');
                }
            } finally {
                fclose($handle);
            }
            if(!rename($tmp,$target)) {
                @unlink($tmp);
                throw new RuntimeException('Cannot finalize private backup');
            }
            return $target;
        } catch (\Throwable $e) {
            if (!$existingSnapshot && $pdo->inTransaction()) $pdo->rollBack();
            throw $e;
        }
    }

    /** Verify format, sha256, and binary data integrity WITHOUT any writes. */
    public static function inspect(string $file): array
    {
        if(!is_file($file) || is_link($file) ||
            ($size=filesize($file))===false || $size<30 || $size>35_000_000) {
            throw new RuntimeException('Invalid CMS backup file');
        }
        $envelope=json_decode((string)file_get_contents($file),true,512,JSON_THROW_ON_ERROR);
        $payload=$envelope['payload']??null;
        if(!is_array($payload) || ($payload['format']??null)!=='celikom-site-content-backup-v1' ||
            !is_string($envelope['sha256']??null) ||
            !hash_equals($envelope['sha256'],hash('sha256',json_encode(
                $payload,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES
            ))) ||
            !is_array($payload['tables']??null) ||
            !is_array($payload['media_data']??null) ||
            array_keys($payload['tables'])!==[
                'content_drafts','site_state','content_revisions','media_assets'
            ]) {
            throw new RuntimeException('CMS backup format or digest mismatch');
        }
        foreach($payload['media_data'] as $key=>$encoded) {
            if(!is_string($key) || !is_string($encoded) ||
                !preg_match('~^site-private/[a-f0-9]{40}\.(?:png|jpg|webp)$~D',$key) ||
                base64_decode($encoded,true)===false) {
                throw new RuntimeException('CMS backup media invalid');
            }
        }
        $expected=[];
        foreach($payload['tables']['media_assets'] as $asset) {
            $key=$asset['storage_key']??null;
            if(!is_string($key) || !isset($payload['media_data'][$key]) ||
                !hash_equals((string)($asset['sha256']??''),hash('sha256',
                    base64_decode($payload['media_data'][$key],true)))) {
                throw new RuntimeException('CMS backup media digest mismatch');
            }
            $expected[$key]=true;
        }
        if(count($expected)!==count($payload['media_data'])) {
            throw new RuntimeException('Unexpected CMS media files');
        }
        return [
            'draft_rows'=>count($payload['tables']['content_drafts']),
            'revision_rows'=>count($payload['tables']['content_revisions']),
            'media_rows'=>count($payload['tables']['media_assets']),
            'published_id'=>$payload['tables']['site_state'][0]['published_revision_id']??null,
        ];
    }

    private static function privatePath(string $path,string $public):bool
    {
        return $path!==$public &&
            !str_starts_with($path,$public.'/') &&
            !str_starts_with($public,$path.'/');
    }
}
