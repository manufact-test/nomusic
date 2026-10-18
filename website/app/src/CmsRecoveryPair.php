<?php
declare(strict_types=1);
namespace Celikom\Website;

use RuntimeException;

/**
 * Stage 10 read-only consistency check of TWO INDEPENDENT CMS backups.
 *
 * Full encrypted DB covers accounts/audit/settings. The separate content
 * snapshot covers site drafts/revisions and private image bytes. Neither
 * alone is a complete recovery. Compare every overlapping row (not merely
 * row counts) to detect an inconsistent pair before attempting any restore.
 *
 * Never writes DB, image or approval files and never includes binary or
 * authentication secrets in its returned report. Does not confer launch
 * approval or promise an atomic server-side backup of a live changing DB.
 */
final class CmsRecoveryPair
{
    private const FIELDS = [
        'content_drafts'=>['id','draft_json','optimistic_version','updated_at'],
        'site_state'=>['id','published_revision_id','updated_at'],
        'content_revisions'=>['id','snapshot_json','change_note','created_at'],
        'media_assets'=>['id','storage_key','original_filename','mime_type',
            'sha256','pixel_width','pixel_height','alt_text','created_at','is_active'],
    ];

    /**
     * @return array{consistent:bool,rows:array<string,int>,media_files:int,published_id:int|null}
     */
    public static function inspect(
        string $fullDbFile, string $contentFile, string $key, string $publicRoot
    ): array {
        $public=realpath($publicRoot);
        $full=self::privateFile($fullDbFile,$public);
        $content=self::privateFile($contentFile,$public);
        if ($full===$content)throw new RuntimeException('Different backup files required');
        // Authenticate entire ciphertext before ever trusting its row callback.
        $dbHeader=CmsFullDbBackup::inspect($full,$key);
        $contentHeader=CmsBackup::inspect($content);
        $envelope=json_decode((string)file_get_contents($content),true,512,JSON_THROW_ON_ERROR);
        $payload=$envelope['payload'];
        $expected=$payload['tables'];
        foreach(self::FIELDS as $table=>$fields) {
            if (!isset($expected[$table]) || !is_array($expected[$table]) ||
                ($dbHeader['tables'][$table]??-1)!==count($expected[$table])) {
                throw new RuntimeException('CMS backups differ in '.$table.' count');
            }
        }
        $dbRows=array_fill_keys(array_keys(self::FIELDS),[]);
        CmsFullDbBackup::inspect($full,$key,
            static function(string $table,array $row) use (&$dbRows):void {
                if(!isset(self::FIELDS[$table]))return;
                $normalized=self::normalize($row,self::FIELDS[$table]);
                $id=$normalized['id'];
                if ($id===null || !ctype_digit($id) || isset($dbRows[$table][$id])) {
                    throw new RuntimeException('Invalid or duplicated full DB CMS key');
                }
                $dbRows[$table][$id]=$normalized;
            }
        );
        foreach(self::FIELDS as $table=>$fields) {
            $observed=[];
            foreach($expected[$table] as $row) {
                if(!is_array($row))throw new RuntimeException('Invalid content backup row');
                $normalized=self::normalize($row,$fields);
                $id=$normalized['id'];
                if($id===null || !ctype_digit($id) || isset($observed[$id])) {
                    throw new RuntimeException('Invalid or duplicated content backup key');
                }
                $observed[$id]=$normalized;
            }
            if($observed!==$dbRows[$table]) {
                // SQL and content JSON both use explicit ordering, but compare
                // by stable id to avoid a false failure on row iteration order.
                ksort($observed,SORT_STRING);
                ksort($dbRows[$table],SORT_STRING);
                if($observed!==$dbRows[$table]) {
                    throw new RuntimeException('Full DB and content differ in '.$table);
                }
            }
        }
        if(count($expected['site_state'])!==1 ||
            (string)($expected['site_state'][0]['id']??'')!=='1') {
            throw new RuntimeException('CMS site state is missing');
        }
        $published=$expected['site_state'][0]['published_revision_id']??null;
        if($published!==null &&
            (!ctype_digit((string)$published) ||
            !isset($dbRows['content_revisions'][(string)$published]))) {
            throw new RuntimeException('Published CMS revision is missing in backup');
        }
        $mediaData=$payload['media_data'];
        foreach($expected['media_assets'] as $asset) {
            $storage=(string)($asset['storage_key']??'');
            $encoded=$mediaData[$storage]??null;
            if(!is_string($encoded))throw new RuntimeException('Missing private media data');
            $bytes=base64_decode($encoded,true);
            if(!is_string($bytes) || strlen($bytes)<30 ||
                strlen($bytes)>CmsMediaStore::MAX_BYTES) {
                throw new RuntimeException('Invalid private media backup bytes');
            }
            $mime=(new \finfo(FILEINFO_MIME_TYPE))->buffer($bytes);
            $size=@getimagesizefromstring($bytes);
            if(!in_array($mime,['image/png','image/jpeg','image/webp'],true) ||
                $mime!==($asset['mime_type']??null) ||
                !is_array($size) || ($size['mime']??null)!==$mime ||
                (int)$size[0]!==(int)($asset['pixel_width']??0) ||
                (int)$size[1]!==(int)($asset['pixel_height']??0) ||
                $size[0]<1 || $size[1]<1 || $size[0]>4096 || $size[1]>4096 ||
                $size[0]*$size[1]>8_388_608) {
                throw new RuntimeException('Private image integrity metadata differs');
            }
        }
        if($contentHeader['media_rows']!==count($mediaData)) {
            throw new RuntimeException('Private media list is incomplete');
        }
        return [
            'consistent'=>true,
            'rows'=>array_map(static fn(array $x):int=>count($x),$dbRows),
            'media_files'=>count($mediaData),
            'published_id'=>$published===null?null:(int)$published,
        ];
    }

    /** @param list<string> $fields
     * @return array<string,string|null>
     */
    private static function normalize(array $row,array $fields):array
    {
        $normalized=[];
        foreach($fields as $field) {
            if(!array_key_exists($field,$row)) {
                throw new RuntimeException('Missing CMS backup field: '.$field);
            }
            if(!is_scalar($row[$field]) && $row[$field]!==null) {
                throw new RuntimeException('Unsupported CMS backup row type');
            }
            $normalized[$field]=$row[$field]===null?null:(string)$row[$field];
        }
        return $normalized;
    }

    private static function privateFile(string $path,string|false $public):string
    {
        clearstatcache(true,$path);
        if(!is_string($public) || !is_dir($public) || is_link($path) ||
            !is_file($path) || ($real=realpath($path))===false ||
            $real===$public || str_starts_with($real,$public.'/') ||
            ($mode=fileperms($path))===false || ($mode&0077)!==0) {
            throw new RuntimeException('Both backup files must be private 0600');
        }
        return $real;
    }
}
