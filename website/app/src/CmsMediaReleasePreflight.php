<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use PDO;
use RuntimeException;

/**
 * Stage 9 read-only preflight of a PRIVATE popup candidate.
 *
 * Deliberately cannot approve rights, encode derivatives, create web-accessible
 * files, mutate revisions or unlock the release gate. Stage 10 requires an
 * independent owner approval and safe derivative generation.
 */
final class CmsMediaReleasePreflight
{
    /** @return array<string,mixed> Non-public metadata, never binary contents. */
    public static function pending(PDO $pdo,string $privateDir,string $publicDir):array
    {
        $choice=CmsMediaAssignment::get($pdo);
        if($choice['asset_id']===null) {
            throw new InvalidArgumentException('Original placeholder is not a release candidate');
        }
        $asset=CmsMediaStore::privatePreview(
            $pdo,$choice['asset_id'],$privateDir,$publicDir
        );
        return self::analyze(
            $choice['asset_id'],$asset['body'],$asset['mime'],$asset['alt']
        );
    }

    /** @return array<string,mixed> */
    public static function analyze(int $assetId,string $bytes,string $mime,string $alt):array
    {
        if($assetId<1 || strlen($bytes)<30 ||
            strlen($bytes)>CmsMediaStore::MAX_BYTES ||
            !in_array($mime,['image/png','image/jpeg','image/webp'],true)) {
            throw new InvalidArgumentException('Invalid private release candidate');
        }
        $actual=(new \finfo(FILEINFO_MIME_TYPE))->buffer($bytes);
        $dimensions=@getimagesizefromstring($bytes);
        if($actual!==$mime || !is_array($dimensions) ||
            ($dimensions['mime']??null)!==$mime ||
            !is_int($dimensions[0]??null) || !is_int($dimensions[1]??null) ||
            $dimensions[0]<1 || $dimensions[1]<1 ||
            $dimensions[0]>4096 || $dimensions[1]>4096 ||
            $dimensions[0]*$dimensions[1]>8_388_608) {
            throw new InvalidArgumentException('Media bytes need format and dimension review');
        }
        if(preg_match('//u',$alt)!==1 || trim($alt)==='' ||
            preg_match_all('/./us',$alt)>300 ||
            preg_match('/[\x00-\x1F\x7F]/',$alt)) {
            throw new InvalidArgumentException('Invalid image ALT');
        }
        // The output is a review fingerprint, not an authorization.
        // In particular, raw uploads may contain EXIF, XMP or other metadata.
        return [
            'asset_id'=>$assetId,
            'sha256'=>hash('sha256',$bytes),
            'mime'=>$mime,
            'bytes'=>strlen($bytes),
            'width'=>$dimensions[0],
            'height'=>$dimensions[1],
            'alt'=>$alt,
            'scope'=>'private_stage9_review_only',
            'public_ready'=>false,
            'stage10_required'=>[
                'owner_rights_and_redaction_confirmation',
                'metadata_stripped_verified_derivative',
                'approved_derivative_checksum_and_visual_qa',
                'separate_joint_website_cms_release_authorization'
            ],
        ];
    }
}
