<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use PDO;
use RuntimeException;

/**
 * Stage 9 only: owner-selectable PRIVATE preview for the sole approved popup
 * media slot. Never written into content_drafts / revisions / public HTML.
 * Future public-media publishing needs independent review in Stage 10.
 */
final class CmsMediaAssignment
{
    private const KEY = 'website.media.popup.pending';

    /** @return array{version:int,asset_id:?int} */
    public static function get(PDO $pdo): array
    {
        $query=$pdo->prepare('SELECT setting_value FROM site_settings WHERE setting_key=?');
        $query->execute([self::KEY]);
        $raw=$query->fetchColumn();
        if($raw===false)return ['version'=>0,'asset_id'=>null];
        return self::decode((string)$raw);
    }

    /** @return int|null Next version, or null for stale owner tab */
    public static function choose(
        PDO $pdo,int $admin,int $expectedVersion,?int $assetId,
        string $privateDir,string $publicDir
    ):?int {
        if($admin<1 || $expectedVersion<0 || $expectedVersion>=PHP_INT_MAX ||
            ($assetId!==null && $assetId<1)) {
            throw new InvalidArgumentException('Invalid private media selection');
        }
        try {
            $pdo->beginTransaction();
            $pdo->prepare('INSERT IGNORE INTO site_settings (setting_key,setting_value,updated_by) ' .
                "VALUES (?,'{\"version\":0,\"asset_id\":null}',?)"
            )->execute([self::KEY,$admin]);
            $read=$pdo->prepare('SELECT setting_value FROM site_settings WHERE setting_key=? FOR UPDATE');
            $read->execute([self::KEY]);
            $current=self::decode((string)$read->fetchColumn());
            if($current['version']!==$expectedVersion) {
                $pdo->rollBack();
                return null;
            }
            if($assetId!==null) {
                // The currently stored original bytes MUST still match the
                // verified upload; neither a revoked nor absent asset is valid.
                CmsMediaStore::privatePreview($pdo,$assetId,$privateDir,$publicDir);
            }
            $next=$expectedVersion+1;
            $json=json_encode(['version'=>$next,'asset_id'=>$assetId],JSON_THROW_ON_ERROR);
            $pdo->prepare('UPDATE site_settings SET setting_value=?,updated_by=? WHERE setting_key=?')
                ->execute([$json,$admin,self::KEY]);
            $pdo->prepare('INSERT INTO audit_log(actor_admin_id,event_name,subject_key,event_metadata) ' .
                'VALUES(?,?,?,?)')->execute([
                $admin,'cms.media.preview.selected',self::KEY,
                json_encode(['asset_id'=>$assetId,'version'=>$next],JSON_THROW_ON_ERROR)
            ]);
            $pdo->commit();
            return $next;
        } catch (\Throwable $e) {
            if($pdo->inTransaction())$pdo->rollBack();
            throw $e;
        }
    }

    /**
     * Replace ONLY the trusted popup image src in the authenticated owner's
     * preview. The v10 file, published snapshots and visitor route unchanged.
     */
    public static function privatePage(
        string $html,?int $assetId,string $alt
    ):string {
        if($assetId===null)return $html;
        if($assetId<1 || preg_match('//u',$alt)!==1 ||
            preg_match('/[\x00-\x1F\x7F]/',$alt) ||
            trim($alt)==='' || preg_match_all('/./us',$alt)>300) {
            throw new InvalidArgumentException('Invalid preview image metadata');
        }
        $search='~<img\b(?=[^>]*\bdata-managed-media="celikom\.popup\.approved")[^>]*>~u';
        if(preg_match_all($search,$html,$matches,PREG_OFFSET_CAPTURE)!==1) {
            throw new RuntimeException('Approved popup image slot not unique');
        }
        $raw=$matches[0][0][0];
        if(substr_count($raw,'src="/media/celikom-popup-approved.png"')!==1 ||
            !preg_match('/\balt="[^"]*"/u',$raw)) {
            throw new RuntimeException('Approved popup media slot changed');
        }
        $src='/admin/?view=media&amp;id='.$assetId;
        $updated=str_replace('src="/media/celikom-popup-approved.png"',
            'src="'.$src.'"',$raw);
        $updated=preg_replace('/\balt="[^"]*"/u','alt="'.Content::escape($alt).'"',$updated,1);
        if(!is_string($updated))throw new RuntimeException('Popup ALT update failed');
        return substr_replace($html,$updated,$matches[0][0][1],strlen($raw));
    }

    /** @return array{version:int,asset_id:?int} */
    private static function decode(string $json):array
    {
        $obj=json_decode($json,true,512,JSON_THROW_ON_ERROR);
        if(!is_array($obj) || array_keys($obj)!==['version','asset_id'] ||
            !is_int($obj['version']) || $obj['version']<0 ||
            ($obj['asset_id']!==null &&
                (!is_int($obj['asset_id']) || $obj['asset_id']<1))) {
            throw new RuntimeException('Invalid media preview selection state');
        }
        return $obj;
    }
}
