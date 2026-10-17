<?php
declare(strict_types=1);
require dirname(__DIR__) . '/app/bootstrap.php';
use Celikom\Website\CommunityDraft;
use Celikom\Website\CommunityFieldCatalog;

$base = dirname(__DIR__);
$html = file_get_contents($base.'/app/Templates/site-v10.html');
$schema = file_get_contents($base.'/app/Config/content-fields-v10.json');
if (!is_string($html) || !is_string($schema)) throw new RuntimeException('Missing v10');
function communityCheck(bool $ok, string $message): void {
    if (!$ok) throw new RuntimeException($message);
}
function communityReject(callable $action, string $name): void {
    try { $action(); } catch (InvalidArgumentException|RuntimeException $expected) { return; }
    throw new RuntimeException('Unsafe edit accepted: '.$name);
}
$fields = CommunityFieldCatalog::fields($schema);
communityCheck(count($fields)===10, 'Ten scoped editable fields required');
communityCheck(count(array_filter($fields,fn($f)=>$f['section']==='contribute'))===8,'Eight contribution fields');
communityCheck(count(array_filter($fields,fn($f)=>$f['section']==='rewards'))===2,'Only two reward headings editable');
foreach ($fields as $key=>$field) {
    CommunityFieldCatalog::check($key,$field['default'],$field);
    communityCheck($field['label']!=='' && $field['section_label']!=='','Missing editor label');
}
communityCheck(CommunityDraft::render($html,$schema,[])===$html,'Default v10 bytes mutated');
$draft=CommunityDraft::render($html,$schema,[
    'contribute.text.02'=>'Какая версия нужна?',
    'contribute.text.05'=>'Сообщить о песне',
    'rewards.text.02'=>'Бонусы за помощь с музыкой',
]);
communityCheck(str_contains($draft,'>Какая версия нужна?<br/>'),'v10 heading geometry changed');
communityCheck(str_contains($draft,'>Сообщить о песне</h3>'),'Offer song card failed');
communityCheck(str_contains($draft,'Бонусы за помощь с музыкой'),'Rewards heading failed');
communityCheck(str_contains($draft,'2% скидки') && str_contains($draft,'20%') &&
    str_contains($draft,'10 песен'),'Earned-percent rule mutated');
$normal = preg_replace('/\s+/u', ' ', $draft);
communityCheck(str_contains($normal,'до запуска оплаты'),'Payment-not-live disclaimer mutated');
communityCheck(substr_count($draft,'<details')===28,'FAQ was modified');
communityCheck(str_contains($draft,'/assets/js/v10/sound-demo.js'),'Original JS gone');
$unsafe=CommunityDraft::render($html,$schema,['contribute.text.05'=>'<script>run()</script>']);
communityCheck(str_contains($unsafe,'&lt;script&gt;run()&lt;/script&gt;'),'Text not escaped');
communityCheck(!str_contains($unsafe,'<script>run()</script>'),'Script injection');
foreach (['rewards.text.03','rewards.text.04','faq.text.01',
    'seo.title','media.popup.alt','hero.lead','how.text.01','install.text.01',
    'contribute.text.09'] as $field) {
    communityReject(fn()=>CommunityDraft::render($html,$schema,[$field=>'rewrite']),$field);
}
communityReject(fn()=>CommunityDraft::render($html,$schema,['contribute.text.05'=>str_repeat('Т',41)]),'layout budget');
communityReject(fn()=>CommunityDraft::render($html,$schema,['contribute.text.06'=>"\x01"]),'control');
communityReject(fn()=>CommunityDraft::render($html,$schema,['rewards.text.01'=>['bad']]),'array');
communityReject(fn()=>CommunityDraft::render($html.' ',$schema,[]),'source blob mismatch');
echo "Stage6: 10 editable v10 community/reward headings; 2%/20% and pending payments locked — PASS\n";
