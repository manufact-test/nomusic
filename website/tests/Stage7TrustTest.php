<?php
declare(strict_types=1);
require dirname(__DIR__) . '/app/bootstrap.php';
use Celikom\Website\TrustDraft;
use Celikom\Website\TrustFieldCatalog;
$base = dirname(__DIR__);
$html = file_get_contents($base.'/app/Templates/site-v10.html');
$manifest = file_get_contents($base.'/app/Config/content-fields-v10.json');
$seed = file_get_contents($base.'/database/seeds/faq-v10.json');
if (!is_string($html) || !is_string($manifest) || !is_string($seed)) {
    throw new RuntimeException('Missing approved v10 sources');
}
function trustAssert(bool $yes, string $label): void {
    if (!$yes) throw new RuntimeException($label);
}
function trustReject(callable $action, string $label): void {
    try { $action(); } catch (InvalidArgumentException|RuntimeException $expected) { return; }
    throw new RuntimeException('Rejected contract accepted: '.$label);
}
$fields = TrustFieldCatalog::fields($manifest);
trustAssert(count($fields) === 10, 'Ten layout-safe heading and list slots');
trustAssert(count(array_filter($fields, fn($f)=>$f['section']==='transparency')) === 6, 'Six transparency copy slots');
trustAssert(count(array_filter($fields, fn($f)=>$f['section']==='faq')) === 4, 'Four FAQ headings and notices');
foreach ($fields as $key=>$field) {
    TrustFieldCatalog::check($key, $field['default'], $field);
    trustAssert($field['label'] !== '' && $field['section_label'] !== '', 'Typed editor label absent');
}
trustAssert(TrustDraft::render($html,$manifest,$seed) === $html, 'Default v10 changed');
$page = TrustDraft::render($html,$manifest,$seed,[
    'transparency.text.02'=>'Понятно про работу CELIKOM.',
    'faq.text.02'=>'Ответы о расширении.',
], [
    'updates'=>['faq-question-27'=>['answer'=>'Проверь вкладку и доступную версию. <script>alert(1)</script>']]
]);
trustAssert(str_contains($page,'Понятно про работу CELIKOM.'),'Trust heading not rendered');
trustAssert(str_contains($page,'Ответы о расширении.'),'FAQ intro heading missing');
trustAssert(str_contains($page,'&lt;script&gt;alert(1)&lt;/script&gt;'),'FAQ XSS not escaped');
trustAssert(!str_contains($page,'<script>alert(1)</script>'),'FAQ script injection');
trustAssert(substr_count($page,'class="faq-item"')===28,'Default FAQ item count changed');
trustAssert(str_contains($page,'не гарантируем неизменность'),'Protected royalty uncertainty changed');
trustAssert(str_contains($page,'не будет подменять'),'Protected fallback changed');
trustAssert(str_contains($page,'Мобильная версия — отдельная разработка'),'Mobile status changed');
trustAssert(str_contains($page,'/assets/js/v10/sound-demo.js'),'Approved JS missing');
foreach ([
    'transparency.text.03','transparency.text.08','transparency.text.09',
    'transparency.text.10','transparency.text.11','transparency.text.12',
    'transparency.text.13','transparency.text.14','rewards.text.03',
    'contribute.text.08','faq-question-27','seo.title'
] as $key) {
    trustReject(fn()=>TrustDraft::render($html,$manifest,$seed,[$key=>'Misleading copy']),$key);
}
foreach (['faq-question-01','faq-question-02','faq-question-04','faq-question-05',
    'faq-question-08','faq-question-09','faq-question-10','faq-question-17',
    'faq-question-18','faq-question-21','faq-question-25'] as $key) {
    trustReject(fn()=>TrustDraft::render($html,$manifest,$seed,[],[
        'updates'=>[$key=>['is_visible'=>false]]
    ]),'protected FAQ '.$key);
}
trustReject(fn()=>TrustDraft::render($html,$manifest,$seed,['faq.text.02'=>str_repeat('я',63)]),'layout limit');
trustReject(fn()=>TrustDraft::render($html,$manifest,$seed,['faq.text.02'=>"\x00"]),'control byte');
trustReject(fn()=>TrustDraft::render($html,$manifest,$seed,['faq.text.02'=>['bad']]),'non-string');
trustReject(fn()=>TrustDraft::render($html.' ',$manifest,$seed),'tampered source');
trustReject(fn()=>TrustDraft::render($html,$manifest,$seed,[],[
    'updates'=>['faq-question-27'=>['category'=>'missing']]
]),'invalid category');
echo "Stage7: immutable v10, 10 safe fields, critical facts locked and FAQ edit/XSS controls — PASS\n";
