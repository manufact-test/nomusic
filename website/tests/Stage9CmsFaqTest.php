<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsEditor;
use Celikom\Website\CmsFaqManager;

function faqMust(bool $value,string $label):void {
    if(!$value)throw new RuntimeException($label);
}
function faqDenied(callable $fn,string $label):void {
    try{$fn();}catch(\InvalidArgumentException|\RuntimeException $expected){return;}
    throw new RuntimeException('Invalid FAQ edit accepted: '.$label);
}
$base=dirname(__DIR__);
$template=file_get_contents($base.'/app/Templates/site-v10.html');
$manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
$seed=file_get_contents($base.'/database/seeds/faq-v10.json');
if(!is_string($template)||!is_string($manifest)||!is_string($seed))
    throw new RuntimeException('Trusted v10 missing');
$fields=CmsEditor::fields($manifest);
faqMust(count($fields)===84,'Combined registry count');
foreach(['hero.title.first','header.link.01','features.text.01','how.text.02',
    'player.text.02','contribute.text.06','rewards.text.02',
    'transparency.text.02','faq.text.02','install.text.02',
    'closing.text.02','footer.text.04','footer.link.02'] as $key){
    faqMust(isset($fields[$key]),'Missing CMS editable section '.$key);
}
faqMust(CmsEditor::validate($template,$manifest,$seed,['content'=>[],'faq'=>[]])===$template,
    'Default CMS render changed approved v10');
$sections=['content'=>[
    'hero.title.first'=>'Возвращаем знакомые песни.',
    'features.text.01'=>'Только проверенные версии',
    'faq.text.02'=>'Помощь и ответы CELIKOM',
    'footer.link.02'=>'#how',
], 'faq'=>[]];
$page=CmsEditor::validate($template,$manifest,$seed,$sections);
faqMust(str_contains($page,'Возвращаем знакомые песни.'),'Hero edit not applied');
faqMust(str_contains($page,'Только проверенные версии'),'Benefits edit not applied');
faqMust(str_contains($page,'Помощь и ответы CELIKOM'),'FAQ heading not applied');
faqMust(str_contains($page,'editor-copy-safety.css'),'Header/Hero edited-preview CSS missing');
faqMust(substr_count($page,'class="faq-item"')===28,'FAQ altered by section edits');
foreach([
    ['rewards.text.03','Меняем 2% на 50%'],
    ['install.status','Установить сейчас'],
    ['transparency.text.14','Гарантируем всем выплаты'],
    ['how.text.03','04'],
    ['sound.result.restored','Danger'],
    ['sound.text.07','Danger'],
    ['footer.link.02','javascript:alert(1)'],
    ['footer.link.02','#faq-question-03'],
    ['hero.primary.href','#unknown-anchor'],
] as [$key,$value]){
    faqDenied(static fn()=>CmsEditor::validate($template,$manifest,$seed,[
        'content'=>[$key=>$value],'faq'=>[]
    ]),'Protected value '.$key);
}
$rows=CmsFaqManager::rows($seed,[]);
faqMust(count($rows)===28,'FAQ seed rows missing');
$protected=array_values(array_filter($rows,static fn($item)=>$item['protected']));
faqMust(count($protected)===18,'Product terms FAQ protection registry changed');
faqDenied(static fn()=>CmsFaqManager::change($seed,[],'faq-question-04',[
    'question'=>'Сколько пробный период?','answer'=>'Всегда бесплатно',
    'category'=>'start','sort_order'=>40,'is_visible'=>false,
]),'Protected FAQ terms hidden');
$original=array_values(array_filter($rows,static fn($item)=>$item['id']==='faq-question-27'))[0];
$changed=CmsFaqManager::change($seed,[],'faq-question-27',[
    'question'=>'Как получить ответ поддержки?',
    'answer'=>'Проверь подключение к интернету и напиши в поддержку.',
    'category'=>$original['category'],
    'sort_order'=>270,
    'is_visible'=>true
]);
$edited=CmsEditor::validate($template,$manifest,$seed,[
    'content'=>[],'faq'=>$changed
]);
faqMust(str_contains($edited,'Как получить ответ поддержки?'),'FAQ edit did not render');
faqMust(str_contains($edited,'Проверь подключение к интернету'),'FAQ answer missing');
faqDenied(static fn()=>CmsFaqManager::change($seed,$changed,'faq-question-27',[
    'question'=>'test','answer'=>'test','category'=>'invalid',
    'sort_order'=>270,'is_visible'=>true
]),'Unknown category');
$new=CmsFaqManager::create($seed,$changed,[
    'category'=>'help','question'=>'Мой новый вопрос?',
    'answer'=>'Ответ на новый вопрос.','sort_order'=>0,'is_visible'=>true,
]);
faqMust(count(CmsFaqManager::rows($seed,$new))===29,'FAQ creation lost item');
faqMust($new['new_items'][0]['is_visible']===false,'New FAQ must start hidden');
$hidden=CmsEditor::validate($template,$manifest,$seed,['content'=>[],'faq'=>$new]);
faqMust(!str_contains($hidden,'Мой новый вопрос?'),'Hidden FAQ leaked to preview');
$visible=CmsFaqManager::change($seed,$new,'faq-question-29',[
    'category'=>'help','question'=>'Мой новый вопрос?',
    'answer'=>'Тест & <> и полезный ответ.','sort_order'=>290,'is_visible'=>true,
]);
$public=CmsEditor::validate($template,$manifest,$seed,['content'=>[],'faq'=>$visible]);
faqMust(str_contains($public,'Мой новый вопрос?'),'New FAQ not visible');
faqMust(str_contains($public,'Тест &amp; &lt;&gt;'),'FAQ escaping failed');
faqMust(substr_count($public,'class="faq-item"')===29,'FAQ count wrong after creation');
faqDenied(static fn()=>CmsEditor::validate($template,$manifest,$seed,[
    'content'=>[],'faq'=>['updates'=>['faq-question-08'=>['answer'=>'Новый тариф']]]
]),'Protected policy FAQ update bypass');
faqDenied(static fn()=>CmsFaqManager::create($seed,$new,[
    'category'=>'help','question'=>'','answer'=>'','sort_order'=>0,'is_visible'=>false,
]),'An invalid empty FAQ should fail at validation');
echo "Stage9: 84 safe section fields, protected FAQ, create/edit/hide/order, v10 parity — PASS\n";
