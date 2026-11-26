<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use PDO;
use RuntimeException;

/**
 * Owner-only private image intake. NEVER serves media to visitors and NEVER
 * changes the approved screenshot source until a separate Stage 10 consent
 * and re-encoding/publishing pipeline is reviewed.
 *
 * On disk: random name, no executable extension, 0600, OUTSIDE public root.
 */
final class CmsMediaStore
{
    public const MAX_BYTES = 2_097_152;
    private const ALLOWED = [
        'image/png'=>'png',
        'image/jpeg'=>'jpg',
        'image/webp'=>'webp',
    ];

    /**
     * @return array{mime:string,extension:string,size:int,width:int,height:int,alt:string,filename:string,sha256:string}
     */
    public static function inspect(string $path,string $filename,string $alt):array
    {
        if(!is_file($path) || is_link($path) || !is_readable($path)) {
            throw new InvalidArgumentException('Media file is not readable');
        }
        $size=filesize($path);
        if(!is_int($size) || $size<30 || $size>self::MAX_BYTES) {
            throw new InvalidArgumentException('Invalid media file size');
        }
        $finfo=new \finfo(FILEINFO_MIME_TYPE);
        $mime=$finfo->file($path);
        if(!is_string($mime) || !isset(self::ALLOWED[$mime])) {
            throw new InvalidArgumentException('Unsupported media MIME');
        }
        $info=@getimagesize($path);
        if(!is_array($info) || ($info['mime']??null)!==$mime ||
            !is_int($info[0]??null) || !is_int($info[1]??null) ||
            $info[0]<1 || $info[1]<1 || $info[0]>4096 || $info[1]>4096 ||
            $info[0]*$info[1]>8_388_608) {
            throw new InvalidArgumentException('Invalid media dimensions or signature');
        }
        if(preg_match('//u',$alt)!==1 ||
            trim($alt)==='' || preg_match_all('/./us',$alt)>300 ||
            preg_match('/[\x00-\x1F\x7F]/',$alt)) {
            throw new InvalidArgumentException('Media ALT required');
        }
        $filename=str_replace('\\','/', $filename);
        $filename=basename($filename);
        if(preg_match('//u',$filename)!==1 || $filename==='' ||
            strlen($filename)>240 || preg_match('/[\x00-\x1F\x7F]/',$filename)) {
            throw new InvalidArgumentException('Invalid original media name');
        }
        $digest=hash_file('sha256',$path);
        if(!is_string($digest))throw new RuntimeException('Cannot hash media');
        return [
            'mime'=>$mime,'extension'=>self::ALLOWED[$mime],
            'size'=>$size,'width'=>$info[0],'height'=>$info[1],
            'alt'=>trim($alt),'filename'=>$filename,'sha256'=>$digest,
        ];
    }

    /**
     * @param array<string,mixed> $file $_FILES entry; must be genuine HTTP upload
     * @return int Persistent private asset ID, not an approved public reference
     */
    public static function accept(
        PDO $pdo,int $admin,array $file,string $alt,
        string $privateDirectory,string $publicDirectory
    ):int {
        if($admin<1 || ($file['error']??null)!==UPLOAD_ERR_OK ||
            !is_string($file['tmp_name']??null) ||
            !is_string($file['name']??null) ||
            !is_int($file['size']??null) ||
            $file['size']>self::MAX_BYTES ||
            !is_uploaded_file($file['tmp_name'])) {
            throw new InvalidArgumentException('Missing or invalid authorized upload');
        }
        $private=realpath($privateDirectory);
        $public=realpath($publicDirectory);
        if(!is_string($private) || !is_dir($private) ||
            !is_string($public) || !is_dir($public) ||
            $private===$public ||
            str_starts_with($private,$public.'/') ||
            str_starts_with($public,$private.'/')) {
            throw new RuntimeException('Private media storage is not isolated from web root');
        }
        $meta=self::inspect($file['tmp_name'],$file['name'],$alt);
        if($meta['size']!==$file['size']) {
            throw new InvalidArgumentException('Upload size changed');
        }
        $key=bin2hex(random_bytes(20)).'.'.$meta['extension'];
        $destination=$private.'/'.$key;
        if(!move_uploaded_file($file['tmp_name'],$destination)) {
            throw new RuntimeException('Cannot move the image to protected storage');
        }
        if(!@chmod($destination,0600)) {
            @unlink($destination);
            throw new RuntimeException('Could not protect private image permissions');
        }
        try {
            $pdo->beginTransaction();
            $pdo->prepare(
                'INSERT INTO media_assets(storage_key,original_filename,mime_type,' .
                'sha256,pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)'
            )->execute([
                'site-private/'.$key,$meta['filename'],$meta['mime'],
                $meta['sha256'],$meta['width'],$meta['height'],$meta['alt'],$admin
            ]);
            $id=(int)$pdo->lastInsertId();
            if($id<1)throw new RuntimeException('Media database insert failed');
            $pdo->prepare(
                'INSERT INTO audit_log(actor_admin_id,event_name,subject_key,event_metadata)' .
                ' VALUES(?,?,?,?)'
            )->execute([$admin,'cms.media.stored',(string)$id,
                json_encode(['mime'=>$meta['mime'],'size'=>$meta['size']],JSON_THROW_ON_ERROR)]);
            $pdo->commit();
            return $id;
        } catch (\Throwable $e) {
            if($pdo->inTransaction())$pdo->rollBack();
            @unlink($destination);
            throw $e;
        }
    }

    /**
     * View a previously checked-in private image ONLY through an authenticated
     * /admin/ request. There is intentionally no public /media/ endpoint.
     * @return array{mime:string,body:string,alt:string}
     */
    public static function privatePreview(
        PDO $pdo,int $assetId,string $storageDirectory,string $publicDirectory
    ):array {
        if($assetId<1)throw new InvalidArgumentException('Invalid image ID');
        $storage=realpath($storageDirectory);
        $public=realpath($publicDirectory);
        if($storage===false || $public===false ||
            $storage===$public ||
            str_starts_with($storage,$public.'/') ||
            str_starts_with($public,$storage.'/')) {
            throw new RuntimeException('Media preview storage is not isolated');
        }
        $q=$pdo->prepare('SELECT storage_key,mime_type,sha256,alt_text FROM media_assets ' .
            'WHERE id=? AND is_active=1 LIMIT 1');
        $q->execute([$assetId]);
        $asset=$q->fetch(PDO::FETCH_ASSOC);
        if(!$asset)throw new InvalidArgumentException('Unknown or inactive image');
        $key=(string)$asset['storage_key'];
        if(!preg_match('~^site-private/([a-f0-9]{40}\.(png|jpg|webp))$~D',$key,$found) ||
            !isset(self::ALLOWED[$asset['mime_type']]) ||
            $found[2]!==self::ALLOWED[$asset['mime_type']]) {
            throw new RuntimeException('Invalid private media reference');
        }
        $path=$storage.'/'.$found[1];
        if(!is_file($path) || is_link($path) ||
            ($size=filesize($path))===false || $size<30 || $size>self::MAX_BYTES) {
            throw new RuntimeException('Private media file unavailable');
        }
        $bytes=file_get_contents($path);
        if(!is_string($bytes) || strlen($bytes)!==$size ||
            !hash_equals((string)$asset['sha256'],hash('sha256',$bytes))) {
            throw new RuntimeException('Private image integrity failed');
        }
        return ['mime'=>(string)$asset['mime_type'],
            'body'=>$bytes,'alt'=>(string)$asset['alt_text']];
    }

    /** @return list<array<string,mixed>> */
    public static function recent(PDO $pdo):array
    {
        $q=$pdo->query('SELECT id,original_filename,mime_type,pixel_width,pixel_height,' .
            'alt_text,created_at FROM media_assets WHERE is_active=1 ORDER BY id DESC LIMIT 20');
        return $q->fetchAll(PDO::FETCH_ASSOC);
    }
}
