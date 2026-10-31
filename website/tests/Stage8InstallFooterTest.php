<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\InstallFooterDraft;
use Celikom\Website\InstallFooterFieldCatalog;
$base=dirname(__DIR__);
$html=file_get_contents($base.'/app/Templates/site-v10.html');
$schema=file_get_contents($base.'/app/Config/content-fields-v10.json');
if (!is_string($html) || !is_string($schema)) throw new RuntimeException('Missing v10');
function installAssert(bool $true,string $label):void{
    if (!$true) throw new RuntimeException($label);
}
function installReject(callable $fn,string $label):void{
    try{$fn();}catch(InvalidArgumentException|RuntimeException $expected){return;}
    throw new RuntimeException('Unsafe Stage 8 change accepted: '.$label);
}
$fields=InstallFooterFieldCatalog::fields($schema);
installAssert(count($fields['texts'])===11,'11 text fields in Stage8');
installAssert(count($fields['links'])===6,'6 safe anchor controls');
foreach($fields['texts'] as $key=>$field){
    InstallFooterFieldCatalog::checkText($key,$field['default'],$field);
}
foreach($fields['links'] as $key=>$field){
    InstallFooterFieldCatalog::checkLink($key,$field['default'],$field,$html);
}
installAssert(InstallFooterDraft::render($html,$schema)===$html,'Byte-identical v10 required');
$rendered=InstallFooterDraft::render($html,$schema,[
    'install.text.02'=>'Подключение после тестирования.',
    'closing.text.02'=>'Музыка, которую помнишь.',
    'closing.text.04'=>'Наверх страницы',
    'footer.text.03'=>'Предложить песню',
],['footer.link.02'=>'#player']);
installAssert(str_contains($rendered,'Подключение после тестирования.'),'Install title missing');
installAssert(str_contains($rendered,'Музыка, которую помнишь.'),'Closing heading missing');
installAssert(str_contains($rendered,'>Предложить песню</a>'),'Footer label missing');
installAssert(str_contains($rendered,'href="#player">Как'),'Footer anchor not updated');
installAssert(str_contains($rendered,'Идёт тестирование'),'Status copy changed');
installAssert(str_contains($rendered,'Пока установка закрыта'),'Installation disabled notice changed');
installAssert(!str_contains($rendered,'>Скачать</a>'),'Invented download CTA');
installAssert(substr_count($rendered,'class="faq-item"')===28,'FAQ changed');
installAssert(str_contains($rendered,'/assets/js/v10/sound-demo.js'),'Original JS changed');
$escaped=InstallFooterDraft::render($html,$schema,['footer.text.04'=>'<svg onload=alert(1)>']);
installAssert(str_contains($escaped,'&lt;svg onload=alert(1)&gt;'),'Text escaping failed');
installAssert(!str_contains($escaped,'<svg onload=alert(1)>'),'Script injection');
foreach(['install.status','install.text.03','install.text.05','install.text.06','install.text.07',
    'rewards.text.03','faq.text.02','footer.link.03'] as $key){
    installReject(fn()=>InstallFooterDraft::render($html,$schema,[$key=>'Ready now']),$key);
}
foreach(['https://example.com/install','javascript:alert(1)','//example.com','#nowhere',
    '#','/download','#faq-question-01'] as $unsafe){
    installReject(fn()=>InstallFooterDraft::render($html,$schema,[],[
        'footer.link.05'=>$unsafe
    ]),'unapproved anchor '.$unsafe);
}
installReject(fn()=>InstallFooterDraft::render($html,$schema,[],['closing.cta.href'=>'#install']),'CTA must point up');
installReject(fn()=>InstallFooterDraft::render($html,$schema,['closing.text.04'=>'Скачать бесплатно']),'false CTA wording');
installReject(fn()=>InstallFooterDraft::render($html,$schema,['footer.text.02'=>str_repeat('Б',31)]),'overflow');
installReject(fn()=>InstallFooterDraft::render($html.' ',$schema),'modified template');
echo "Stage8: closed installation, 11 text fields, 6 local anchors and original v10 structure — PASS\n";
