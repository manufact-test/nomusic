<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use PDO;
use RuntimeException;

/**
 * Stage 9: produce an UNAPPROVED metadata-stripped PNG for an offline owner review.
 * Never writes into public_html, changes a CMS revision, approves rights or
 * creates the Stage 10 release marker. Caller must supply a separate 0700 dir.
 */
final class CmsMediaDerivative
{
    public static function preparePending(
        PDO $pdo,string $privateMediaDir,string $reviewDir,string $publicDir
    ):array {
        if(!extension_loaded('gd')) {
            throw new RuntimeException('GD decoder not installed');
        }
        $media=realpath($privateMediaDir);
        $review=realpath($reviewDir);
        $public=realpath($publicDir);
        if(!is_string($media) || !is_string($review) || !is_string($public) ||
            !is_dir($media) || !is_dir($review) || !is_dir($public)) {
            throw new RuntimeException('Invalid derivative directories');
        }
        // Avoid both direct public paths and overlapping original/review storage.
        foreach([$media,$review] as $path) {
            if($path===$public || str_starts_with($path,$public.'/') ||
                str_starts_with($public,$path.'/')) {
                throw new RuntimeException('Derivative storage cannot overlap public root');
            }
        }
        if($media===$review || str_starts_with($media,$review.'/') ||
            str_starts_with($review,$media.'/') ||
            (fileperms($review)&0077)!==0 || !is_writable($review)) {
            throw new RuntimeException('Derivative review directory must be separate and private');
        }
        $selected=CmsMediaAssignment::get($pdo);
        if($selected['asset_id']===null) {
            throw new InvalidArgumentException('No private popup selected for review');
        }
        $id=$selected['asset_id'];
        $asset=CmsMediaStore::privatePreview($pdo,$id,$media,$public);
        $source=CmsMediaReleasePreflight::analyze(
            $id,$asset['body'],$asset['mime'],$asset['alt']
        );
        $decoded=@imagecreatefromstring($asset['body']);
        if(!$decoded instanceof \GdImage) {
            throw new InvalidArgumentException('Source cannot be decoded for safe export');
        }
        $canvas=null;
        $tmp=null;
        try {
            $width=$source['width'];
            $height=$source['height'];
            $canvas=imagecreatetruecolor($width,$height);
            if(!$canvas instanceof \GdImage) {
                throw new RuntimeException('Cannot allocate derivative image');
            }
            imagealphablending($canvas,false);
            imagesavealpha($canvas,true);
            $clear=imagecolorallocatealpha($canvas,0,0,0,127);
            imagefill($canvas,0,0,$clear);
            if(!imagecopy($canvas,$decoded,0,0,0,0,$width,$height)) {
                throw new RuntimeException('Cannot copy decoded pixels');
            }
            $tmp=$review.'/.candidate-'.bin2hex(random_bytes(16)).'.tmp';
            $fd=fopen($tmp,'x+b');
            if($fd===false)throw new RuntimeException('Cannot allocate private derivative');
            fclose($fd);
            if(!chmod($tmp,0600))throw new RuntimeException('Unsafe derivative permissions');
            // Fresh encoder drops input EXIF, ICC, XMP and PNG ancillary chunks.
            if(!@imagepng($canvas,$tmp,8)) {
                throw new RuntimeException('Derivative PNG encoding failed');
            }
            clearstatcache(true,$tmp);
            $size=filesize($tmp);
            if(!is_int($size) || $size<30 || $size>10_485_760 ||
                is_link($tmp) || (fileperms($tmp)&0077)!==0) {
                throw new RuntimeException('Unsafe derivative file');
            }
            $bytes=file_get_contents($tmp);
            if(!is_string($bytes) || strlen($bytes)!==$size) {
                throw new RuntimeException('Could not verify derivative bytes');
            }
            $out=CmsMediaReleasePreflight::analyze($id,$bytes,'image/png',$asset['alt']);
            if($out['width']!==$width || $out['height']!==$height) {
                throw new RuntimeException('Derivative geometry mismatch');
            }
            // Owner can switch the image in another tab during encoding.
            if(CmsMediaAssignment::get($pdo)!==$selected) {
                throw new RuntimeException('Private popup selection changed during preparation');
            }
            $name='candidate-'.bin2hex(random_bytes(20)).'.png';
            if(!rename($tmp,$review.'/'.$name)) {
                throw new RuntimeException('Could not finalize private derivative');
            }
            $tmp=null;
            return [
                'asset_id'=>$id,
                'selection_version'=>$selected['version'],
                'source_sha256'=>$source['sha256'],
                'derivative_sha256'=>$out['sha256'],
                'derivative_filename'=>$name,
                'mime'=>'image/png',
                'width'=>$width,
                'height'=>$height,
                'bytes'=>$size,
                'scope'=>'private_stage9_review_only',
                'public_ready'=>false,
                'requires_owner_rights_review'=>true,
                'requires_visual_review'=>true,
            ];
        } finally {
            if($canvas instanceof \GdImage)imagedestroy($canvas);
            imagedestroy($decoded);
            if($tmp!==null && is_file($tmp))@unlink($tmp);
        }
    }
}
