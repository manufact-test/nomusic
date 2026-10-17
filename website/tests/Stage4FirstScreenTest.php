<?php
declare(strict_types=1);
require dirname(__DIR__) . '/app/bootstrap.php';

use Celikom\Website\FirstScreenDraft;

$base = dirname(__DIR__);
$template = file_get_contents($base . '/app/Templates/site-v10.html');
$manifest = file_get_contents($base . '/app/Config/content-fields-v10.json');
if (!is_string($template) || !is_string($manifest)) {
    throw new RuntimeException('Missing trusted v10 template/registry');
}
function verifyFirstScreen(bool $ok, string $message): void {
    if (!$ok) throw new RuntimeException($message);
}
function rejectFirstScreen(callable $callback, string $message): void {
    try { $callback(); } catch (InvalidArgumentException|RuntimeException $expected) { return; }
    throw new RuntimeException('Unsafe first-screen operation accepted: ' . $message);
}

// Initial approved HTML cannot be serialized, reformatted or redrawn.
verifyFirstScreen(FirstScreenDraft::render($template, $manifest, []) === $template, 'Default draft drifted from v10');

// Isolated Header+Hero+Demo edits, with the original CSS, JS and FAQ untouched.
$draft = FirstScreenDraft::render($template, $manifest, [
    'header.text.02' => 'Почему CELIKOM',
    'hero.title.first' => 'Знакомые песни.',
    'hero.lead' => 'Короткое описание для редактора & без <script>.',
    'hero.primary.href' => '#sound',
    'sound.text.01' => 'Демонстрация принципа',
]);
verifyFirstScreen(str_contains($draft, '>Почему CELIKOM</a>'), 'Header field missing');
verifyFirstScreen(str_contains($draft, '<h1>Знакомые песни.<br/>'), 'Hero structure changed');
verifyFirstScreen(str_contains($draft, '#sound'), 'Safe Hero anchor not applied');
verifyFirstScreen(str_contains($draft, 'Короткое описание для редактора &amp; без &lt;script&gt;.'), 'Unsafe HTML in Hero');
verifyFirstScreen(str_contains($draft, '>Демонстрация принципа</div>'), 'Demo field missing');
verifyFirstScreen(str_contains($draft, 'data-managed-media="celikom.popup.approved"'), 'Real popup media contract missing');
verifyFirstScreen(substr_count($draft, '<details') === 28, 'FAQ markup modified');
verifyFirstScreen(str_contains($draft, '/assets/css/v10/04-v10.css'), 'Original v10 CSS missing');
verifyFirstScreen(str_contains($draft, '/assets/js/v10/sound-demo.js'), 'Original demo JS missing');

// A first-screen editor must not be able to reach global FAQ, SEO, media
// or other page fields, even though the full content manifest contains them.
rejectFirstScreen(static fn() => FirstScreenDraft::render($template, $manifest, ['seo.title' => 'Hello']), 'SEO edit');
rejectFirstScreen(static fn() => FirstScreenDraft::render($template, $manifest, ['media.popup.alt' => 'Fake']), 'media attr edit');
rejectFirstScreen(static fn() => FirstScreenDraft::render($template, $manifest, ['faq.text.01' => 'Fake']), 'FAQ edit');
rejectFirstScreen(static fn() => FirstScreenDraft::render($template, $manifest, ['rewards.text.01' => 'Fake']), 'other section');
rejectFirstScreen(static fn() => FirstScreenDraft::render($template, $manifest, ['hero.primary.href' => '//evil.example']), 'protocol-relative URL');
rejectFirstScreen(static fn() => FirstScreenDraft::render($template, $manifest, ['hero.primary.href' => 'javascript:alert(1)']), 'script URL');
$safe = FirstScreenDraft::render($template, $manifest, ['hero.eyebrow' => '<img onerror=alert(1)>']);
verifyFirstScreen(str_contains($safe, '&lt;img onerror=alert(1)&gt;'), 'Hero eyebrow was not escaped');

rejectFirstScreen(static fn() => FirstScreenDraft::render($template, $manifest, ['hero.title.first' => str_repeat('X', 2000)]), 'text length');
rejectFirstScreen(static fn() => FirstScreenDraft::render($template . ' ', $manifest, []), 'mutated trusted template');
echo "Stage 4 first-screen scope: Header, Hero, demo edit guard and unchanged v10 — PASS\n";
