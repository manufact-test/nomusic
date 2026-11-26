<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * Reviewed v10 metadata slots: title, description and accessible popup ALT.
 * OG images, robots directives, canonical URL and screenshot source paths
 * remain code-controlled until final owner and media approval.
 */
final class CmsSeoCatalog
{
    private const KEYS = [
        'seo.title'=>['text_fields','head','title',70],
        'seo.description'=>['attribute_fields','head','meta',320],
        'media.popup.alt'=>['attribute_fields','top','img',300],
    ];

    /** @return array<string,array<string,mixed>> */
    public static function fields(string $json): array
    {
        $manifest=json_decode($json,true,512,JSON_THROW_ON_ERROR);
        if(!is_array($manifest)||($manifest['version']??null)!==1) {
            throw new RuntimeException('Invalid v10 manifest');
        }
        $out=[];
        foreach(self::KEYS as $key=>[$bucket,$section,$tag,$limit]) {
            $found=[];
            foreach($manifest[$bucket]??[] as $field) {
                if(($field['key']??null)===$key) $found[]=$field;
            }
            if(count($found)!==1 || ($found[0]['section']??null)!==$section ||
                ($found[0]['tag']??null)!==$tag ||
                !is_string($found[0]['default']??null) ||
                ($found[0]['max_chars']??null)<$limit) {
                throw new RuntimeException('Unapproved metadata slot');
            }
            $field=$found[0];
            $out[$key]=[
                'key'=>$key,'section'=>$section,
                'section_label'=>$key==='media.popup.alt'?'Доступность медиа':'SEO',
                'label'=>(string)($field['label']??$key),
                'default'=>$field['default'],'max_chars'=>$limit,
                'type'=>'metadata',
            ];
        }
        return $out;
    }

    public static function check(string $key,string $value,array $field):void
    {
        if(!isset(self::KEYS[$key]) || ($field['key']??null)!==$key ||
            ($field['type']??null)!=='metadata' ||
            preg_match('//u',$value)!==1 ||
            preg_match('/[\x00-\x1F\x7F]/',$value)) {
            throw new InvalidArgumentException('Invalid SEO metadata');
        }
        $length=preg_match_all('/./us',trim($value));
        if(trim($value)==='' || $length===false ||
            $length>$field['max_chars'] ||
            strlen($value)>4*$field['max_chars']) {
            throw new InvalidArgumentException('Metadata exceeds approved budget');
        }
    }
}
