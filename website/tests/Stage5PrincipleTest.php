<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\PrincipleDraft;
use Celikom\Website\PrincipleFieldCatalog;

$base = dirname(__DIR__);
$template = file_get_contents($base.'/app/Templates/site-v10.html');
$manifest = file_get_contents($base.'/app/Config/content-fields-v10.json');
if (!is_string($template) || !is_string($manifest)) throw new RuntimeException('Missing Stage 5 source');
function principleOK(bool $ok, string $message): void {
    if (!$ok) throw new RuntimeException($message);
}
function principleReject(callable $call, string $case): void {
    try { $call(); } catch (InvalidArgumentException|RuntimeException $expected) { return; }
    throw new RuntimeException('Unsafe Stage 5 field accepted: '.$case);
}
$fields = PrincipleFieldCatalog::fields($manifest);
principleOK(count($fields) === 22, 'Stage 5 should expose exactly 22 typed fields');
principleOK(count(array_filter($fields, static fn($x) => $x['section']==='features'))===6,'Benefits 6 fields');
principleOK(count(array_filter($fields, static fn($x) => $x['section']==='how'))===8,'Steps 8 fields');
principleOK(count(array_filter($fields, static fn($x) => $x['section']==='player'))===8,'Player 8 fields');
foreach ($fields as $key=>$field) {
    PrincipleFieldCatalog::check($key, $field['default'], $field);
    principleOK($field['label']!=='' && $field['section_label']!=='', 'Missing labels');
}
principleOK(PrincipleDraft::render($template,$manifest,[])===$template,'Original v10 byte parity');
$edits = [
    'features.text.01'=>'Знакомые версии',
    'how.text.02'=>'Три простых шага',
    'how.text.04'=>'Подключение после запуска',
    'how.text.05'=>'Сейчас установка закрыта, после запуска открой страницу и следуй инструкции.',
    'player.text.02'=>'Плеер остаётся.',
    'player.text.03'=>'Звук меняется.',
    'player.text.08'=>'Перемотать'
];
$html = PrincipleDraft::render($template,$manifest,$edits);
foreach ($edits as $text) principleOK(str_contains($html, htmlspecialchars($text, ENT_QUOTES|ENT_SUBSTITUTE|ENT_HTML5,'UTF-8')), 'Edited text missing');
principleOK(str_contains($html, '<div class="num">01</div>') &&
    str_contains($html, '<div class="num">02</div>') &&
    str_contains($html, '<div class="num">03</div>'), 'Immutable step numbers changed');
principleOK(substr_count($html, '<details')===28,'FAQ modified');
principleOK(str_contains($html,'/assets/js/v10/sound-demo.js'),'Original JS modified');
principleOK(str_contains($html,'data-managed-media="celikom.popup.approved"'),'Media policy altered');
$untrusted = PrincipleDraft::render($template,$manifest,['features.text.01'=>'<script>alert(1)</script>']);
principleOK(str_contains($untrusted,'&lt;script&gt;alert(1)&lt;/script&gt;'),'Escaping missing');
principleOK(!str_contains($untrusted,'<script>alert(1)</script>'),'Script injection passed');
foreach (['how.text.03','how.text.06','how.text.09','hero.lead','sound.text.01','faq.text.01','seo.title','media.popup.alt','rewards.text.01'] as $key) {
    principleReject(static fn()=>PrincipleDraft::render($template,$manifest,[$key=>'changed']), $key);
}
principleReject(static fn()=>PrincipleDraft::render($template,$manifest,['features.text.01'=>str_repeat('X',37)]),'overlong card');
principleReject(static fn()=>PrincipleDraft::render($template,$manifest,['player.text.05'=>"\x01"]),'control char');
principleReject(static fn()=>PrincipleDraft::render($template,$manifest,['how.text.04'=>['array']]),'array');
principleReject(static fn()=>PrincipleDraft::render($template.' ',$manifest,[]),'modified template');
echo "Stage 5 catalog and preview: 22 copy fields, steps 01/02/03 fixed, exact v10, XSS/scope — PASS\n";
