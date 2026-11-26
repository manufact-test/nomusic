<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\CmsEditor;
use Celikom\Website\CmsSeoCatalog;
use Celikom\Website\CmsMediaStore;

function mediaAssert(bool $v,string $m):void { if(!$v)throw new RuntimeException($m); }
function mediaReject(callable $fn,string $why):void {
    try{$fn();}catch(InvalidArgumentException|RuntimeException $e){return;}
    throw new RuntimeException('Unsafe content accepted: '.$why);
}
$base=dirname(__DIR__);
$html=file_get_contents($base.'/app/Templates/site-v10.html');
$manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
$seed=file_get_contents($base.'/database/seeds/faq-v10.json');
if(!is_string($html)||!is_string($manifest)||!is_string($seed))throw new RuntimeException('v10 missing');
$seo=CmsSeoCatalog::fields($manifest);
mediaAssert(count($seo)===3,'SEO/ALT catalog count');
mediaAssert(count(CmsEditor::fields($manifest))===87,'Combined field count');
mediaAssert(CmsEditor::validate($html,$manifest,$seed,['content'=>[],'faq'=>[]])===$html,'Default v10 parity');
$rendered=CmsEditor::validate($html,$manifest,$seed,['content'=>[
    'seo.title'=>'Новое название & тест',
    'seo.description'=>'CELIKOM — "описание" & справка',
    'media.popup.alt'=>'Интерфейс <расширения> & кнопки',
], 'faq'=>[]]);
mediaAssert(str_contains($rendered,'Новое название &amp; тест'),'SEO title escaping');
mediaAssert(str_contains($rendered,'CELIKOM — &quot;описание&quot; &amp; справка'),'SEO description escaping');
mediaAssert(str_contains($rendered,'Интерфейс &lt;расширения&gt; &amp; кнопки'),'Media ALT escaping');
mediaAssert(str_contains($rendered,'/media/celikom-popup-approved.png'),'Approved image source retained');
mediaAssert(!str_contains($rendered,'<расширения>'),'Unsafe rendered markup');
foreach([
    ['seo.description',''],
    ['seo.title',str_repeat('Я',71)],
    ['media.popup.alt',str_repeat('а',301)],
    ['media.popup.approved','/uploads/unknown.png'],
    ['seo.robots','index,follow'],
] as [$key,$value]){
    mediaReject(fn()=>CmsEditor::validate($html,$manifest,$seed,['content'=>[$key=>$value],'faq'=>[]]),$key);
}
$file=tempnam(sys_get_temp_dir(),'celikom-picture');
if(!is_string($file))throw new RuntimeException('Cannot create fixture');
try {
    // Synthetic 1x1 pixel PNG: not the real user screenshot.
    $fixture=base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true);
    if(!is_string($fixture))throw new RuntimeException('Test fixture decode');
    file_put_contents($file,$fixture);
    $meta=CmsMediaStore::inspect($file,'test.png','Тестовое изображение');
    mediaAssert($meta['mime']==='image/png' &&
        $meta['width']===1 && $meta['height']===1,'Private PNG rejected');
    mediaAssert(strlen($meta['sha256'])===64,'Missing SHA');
    mediaReject(fn()=>CmsMediaStore::inspect($file,'x.png',''),'ALT omission');
    mediaReject(fn()=>CmsMediaStore::inspect($file,'x.png',str_repeat('т',301)),'ALT size');
    mediaReject(fn()=>CmsMediaStore::inspect($file,"path\0.png",'Valid ALT'),'Bad filename');
    file_put_contents($file,'<svg onload="alert(1)"></svg>');
    mediaReject(fn()=>CmsMediaStore::inspect($file,'evil.svg','Valid ALT'),'SVG code');
    file_put_contents($file,str_repeat('X',CmsMediaStore::MAX_BYTES+1));
    mediaReject(fn()=>CmsMediaStore::inspect($file,'large.png','Valid ALT'),'Oversized file');
} finally {
    @unlink($file);
}
echo "Stage9: SEO and ALT escaping; private image signature, dimensions and limits — PASS\n";
