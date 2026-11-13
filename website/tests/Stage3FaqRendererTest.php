<?php
declare(strict_types=1);
require dirname(__DIR__) . '/app/bootstrap.php';

use Celikom\Website\FaqV10Renderer;
use Celikom\Website\V10Renderer;

function check(bool $ok, string $message): void {
    if (!$ok) throw new RuntimeException($message);
}
function rejected(callable $try, string $name): void {
    try { $try(); } catch (InvalidArgumentException|RuntimeException $expected) { return; }
    throw new RuntimeException('Expected FAQ rejection: ' . $name);
}

$root = dirname(__DIR__);
$html = file_get_contents($root . '/app/Templates/site-v10.html');
$schema = file_get_contents($root . '/app/Config/content-fields-v10.json');
$seed = file_get_contents($root . '/database/seeds/faq-v10.json');
check(is_string($html) && is_string($schema) && is_string($seed), 'Missing approved v10 resources');

check(FaqV10Renderer::render($html, $seed) === $html, 'Default FAQ must preserve exact v10 bytes');
check(FaqV10Renderer::render($html, $seed, ['updates'=>[],'new_items'=>[]]) === $html, 'Empty FAQ draft mutated v10');
check(substr_count($html, '<details class="faq-item"') === 28, 'The base template needs 28 FAQs');

$edited = FaqV10Renderer::render($html, $seed, [
    'updates' => [
        'faq-question-01' => ['question' => 'Привет <script>alert(1)</script> & тест?', 'answer'=>'Тест "&" <img src=x onerror=alert(1)>'],
        'faq-question-04' => ['category'=>'help','sort_order'=>850],
        'faq-question-02' => ['is_visible'=>false],
        'faq-question-05' => ['sort_order'=>5],
    ],
    'new_items' => [
        [
            'id'=>'faq-question-29','category'=>'rewards','question'=>'Новый FAQ — тест',
            'answer'=>'Ответ & только простой текст','sort_order'=>65,'is_visible'=>true,
        ],
    ],
]);
check(substr_count($edited, '<details class="faq-item"') === 28, 'One hidden and one new must remain 28');
check(!str_contains($edited, '<script>alert(1)</script>'), 'FAQ question XSS was not escaped');
check(!str_contains($edited, '<img src=x'), 'FAQ answer XSS was not escaped');
check(str_contains($edited, 'Привет &lt;script&gt;alert(1)&lt;/script&gt; &amp; тест?'), 'FAQ question escaping');
check(str_contains($edited, '<p>Тест &quot;&amp;&quot; &lt;img src=x onerror=alert(1)&gt;</p>'), 'FAQ answer escaping');
check(str_contains($edited, 'data-category="help" id="faq-question-04"'), 'FAQ recategorization');
check(!str_contains($edited, 'id="faq-question-02"'), 'FAQ visibility toggle failed');
check(str_contains($edited, 'id="faq-question-29"'), 'FAQ new item not added');
check(strpos($edited, 'id="faq-question-05"') < strpos($edited, 'id="faq-question-01"'), 'Sorting did not reorder items');
check(strpos($edited, 'id="faq-question-29"') < strpos($edited, 'id="faq-question-04"'), 'New item sort position wrong');
check(str_contains($edited, 'class="faq-empty" hidden="" id="faq-empty"'), 'Filter empty state removed');
check(str_contains($edited, 'data-filter="rewards"'), 'Original client-side filters removed');
check(str_contains($edited, 'В этой теме пока нет вопросов.'), 'Original fallback was removed');

// FAQs render after CMS text fields: edits in Hero must not corrupt FAQ source.
$copyChanged = V10Renderer::render($html, $schema, ['hero.title.first'=>'Те самые версии']);
$joint = FaqV10Renderer::render($copyChanged, $seed, ['updates'=>[
    'faq-question-01' => ['answer'=>'Содержание FAQ из будущей админки'],
]]);
check(str_contains($joint, '<h1>Те самые версии<br/>'), 'Hero binding lost in FAQ render');
check(str_contains($joint, '<p>Содержание FAQ из будущей админки</p>'), 'FAQ binding lost');
check(FaqV10Renderer::render($copyChanged, $seed) === $copyChanged, 'Unchanged FAQ must not alter edited content');

rejected(static fn()=>FaqV10Renderer::render(str_replace('id="faq-list"', 'id="other-faq-list"', $html), $seed), 'FAQ list wrapper mutation');
// Alter the source FAQ itself to simulate unexpectedly changed publisher template.
rejected(static fn()=>FaqV10Renderer::render(str_replace('Что такое CELIKOM?', 'Иная версия?', $html), $seed), 'unapproved FAQ markup');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['updates'=>['faq-question-99'=>['question'=>'oops']]]), 'unknown FAQ ID');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['updates'=>['faq-question-01'=>['answer_html'=>'<script>x</script>']]]), 'raw HTML field');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['updates'=>['faq-question-01'=>['category'=>'unsafe']]]), 'unknown category');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['updates'=>['faq-question-01'=>['is_visible'=>'false']]]), 'wrong visibility type');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['updates'=>['faq-question-01'=>['sort_order'=>-1]]]), 'negative sort order');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['updates'=>['faq-question-01'=>['question'=>'']]]), 'empty question');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['new_items'=>[
    ['id'=>'faq-question-01','category'=>'start','question'=>'duplicate','answer'=>'answer','sort_order'=>300,'is_visible'=>true],
]]), 'duplicate ID');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['updates'=>['faq-question-01'=>['question'=>str_repeat('x', 401)]]]), 'overlong question');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['unknown'=>true]), 'unknown top-level operation');
rejected(static fn()=>FaqV10Renderer::render($html, $seed, ['new_items'=>[
    ['id'=>'faq-question-29','category'=>'start','question'=>'One','answer'=>'one','sort_order'=>290,'is_visible'=>true],
    ['id'=>'faq-question-29','category'=>'start','question'=>'Two','answer'=>'two','sort_order'=>300,'is_visible'=>true],
]]), 'duplicate new ID');

echo "FAQ v10: 28 exact default items + safe editor changes, visibility, categories, ordering, add and XSS guards — PASS\n";
