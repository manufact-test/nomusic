<?php
declare(strict_types=1);
namespace Celikom\Website;

use InvalidArgumentException;
use RuntimeException;

/**
 * FAQ controller model for Stage 9. Existing protected product/legal answers
 * cannot be edited/hidden/reordered. Category definitions stay canonical.
 * Converts simple admin forms into the approved FaqV10Renderer draft format.
 */
final class CmsFaqManager
{
    /** @return list<array<string,mixed>> */
    public static function rows(string $seedJson, array $draft = []): array
    {
        $seed = json_decode($seedJson, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($seed) || ($seed['version'] ?? null) !== 1 ||
            !is_array($seed['items'] ?? null) || count($seed['items']) !== 28) {
            throw new RuntimeException('Invalid canonical FAQ seed');
        }
        if (array_diff(array_keys($draft),['updates','new_items']) !== []) {
            throw new InvalidArgumentException('Unapproved FAQ operation');
        }
        $updates=$draft['updates']??[];
        $new=$draft['new_items']??[];
        if (!is_array($updates) || !is_array($new) || !array_is_list($new)) {
            throw new InvalidArgumentException('Malformed FAQ draft');
        }
        $rows=[];
        foreach ($seed['items'] as $seedItem) {
            $id=$seedItem['id'];
            $row=[
                'id'=>$id,
                'category'=>$seedItem['category'],
                'question'=>$seedItem['question'],
                'answer'=>substr((string)$seedItem['answer_html'],3,-4),
                'sort_order'=>$seedItem['sort_order'],
                'is_visible'=>$seedItem['is_visible'],
                'protected'=>TrustDraft::isProtectedFaqId($id),
            ];
            if(isset($updates[$id])) {
                if (!is_array($updates[$id]) || $row['protected']) {
                    throw new InvalidArgumentException('Protected or malformed FAQ update');
                }
                $row=array_merge($row,$updates[$id]);
            }
            $rows[]=$row;
        }
        foreach ($new as $item) {
            if(!is_array($item)) throw new InvalidArgumentException('Invalid new FAQ item');
            $rows[]=array_merge($item,['protected'=>false]);
        }
        usort($rows,static fn(array $a,array $b):int=>
            ($a['sort_order']<=>$b['sort_order']) ?: strcmp($a['id'],$b['id']));
        return $rows;
    }

    /**
     * @param array<string,mixed> $current
     * @param array<string,mixed> $form
     * @return array<string,mixed>
     */
    public static function change(string $seedJson,array $current,string $id,array $form):array
    {
        $rows=self::rows($seedJson,$current);
        $exists=false;
        foreach($rows as $item) {
            if($item['id']===$id) {
                if($item['protected'])throw new InvalidArgumentException('Protected FAQ');
                $exists=true;
                break;
            }
        }
        if(!$exists)throw new InvalidArgumentException('Unknown FAQ item');
        $values=self::reviewFields($form);
        $next=$current;
        if (isset($next['updates'][$id]) || preg_match('/^faq-question-(0[1-9]|1[0-9]|2[0-8])$/D',$id)) {
            $next['updates'][$id]=$values;
        } else {
            $replaced=false;
            foreach($next['new_items']??[] as &$item) {
                if($item['id']===$id) {
                    $item=array_merge($item,$values);
                    $replaced=true;
                    break;
                }
            }
            unset($item);
            if(!$replaced)throw new InvalidArgumentException('Missing new FAQ');
        }
        return $next;
    }

    /** @param array<string,mixed> $current @param array<string,mixed> $form */
    public static function create(string $seedJson,array $current,array $form):array
    {
        $rows=self::rows($seedJson,$current);
        $max=28;
        $order=0;
        foreach($rows as $row) {
            if(!preg_match('/^faq-question-([0-9]{2,4})$/D',$row['id'],$m)) {
                throw new InvalidArgumentException('Invalid FAQ ID');
            }
            $max=max($max,(int)$m[1]);
            $order=max($order,(int)$row['sort_order']);
        }
        if($max>=9999 || count($rows)>=100)throw new InvalidArgumentException('FAQ capacity exceeded');
        $fields=self::reviewFields([
            'category'=>$form['category']??null,
            'question'=>$form['question']??null,
            'answer'=>$form['answer']??null,
            'sort_order'=>$order+10,
            'is_visible'=>false, // requires explicit review before public visibility
        ]);
        $item=array_merge(['id'=>'faq-question-'.str_pad((string)($max+1),2,'0',STR_PAD_LEFT)],$fields);
        $next=$current;
        $next['new_items'][]=$item;
        return $next;
    }

    /** @return array<string,mixed> */
    private static function reviewFields(array $form):array
    {
        $allowed=['category','question','answer','sort_order','is_visible'];
        if(array_diff(array_keys($form),$allowed)!==[] ||
            array_diff($allowed,array_keys($form))!==[]) {
            throw new InvalidArgumentException('Incomplete FAQ form');
        }
        if(!is_string($form['category']) ||
            !in_array($form['category'],['start','rewards','music','help'],true) ||
            !is_string($form['question']) ||
            !is_string($form['answer']) ||
            !is_int($form['sort_order']) ||
            $form['sort_order']<0 || $form['sort_order']>100000 ||
            !is_bool($form['is_visible'])) {
            throw new InvalidArgumentException('Invalid FAQ form type');
        }
        foreach (['question'=>400, 'answer'=>3000] as $key=>$max) {
            $value=trim($form[$key]);
            if($value==='' || preg_match('//u',$value)!==1 ||
                strlen($value)>$max*4 ||
                preg_match('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/',$value) ||
                preg_match_all('/./us',$value)>$max) {
                throw new InvalidArgumentException('FAQ text exceeds approved budget');
            }
        }
        return $form;
    }
}
