<?php
declare(strict_types=1);
require dirname(__DIR__) . '/app/bootstrap.php';

use Celikom\Website\V10Renderer;

function ensure(bool $ok, string $message): void
{
    if (!$ok) {
        throw new RuntimeException($message);
    }
}
function refuses(callable $fn, string $message): void
{
    try {
        $fn();
    } catch (InvalidArgumentException|RuntimeException $expected) {
        return;
    }
    throw new RuntimeException('Unexpected success: ' . $message);
}

$base = dirname(__DIR__);
$template = file_get_contents($base . '/app/Templates/site-v10.html');
$schema = file_get_contents($base . '/app/Config/content-fields-v10.json');
ensure(is_string($template) && is_string($schema), 'Missing site template or schema');
$manifest = json_decode($schema, true, 512, JSON_THROW_ON_ERROR);
ensure(count($manifest['text_fields']) === 91, 'Expected 91 editable text nodes');
ensure(count($manifest['link_fields']) === 13, 'Expected 13 CMS links');
ensure(count($manifest['media_fields']) === 1, 'Expected media placeholder');
ensure(count($manifest['attribute_fields']) === 2, 'Expected SEO and accessibility metadata');

ensure(V10Renderer::render($template, $schema) === $template, 'Default render modified v10');
ensure(V10Renderer::render($template, $schema, ['hero.title.first' => "Те самые песни."]) === $template, 'Unchanged text modified v10');

$rendered = V10Renderer::render($template, $schema, [
    'hero.title.first' => 'Знакомые песни',
    'hero.title.accent' => 'И снова вместе!',
    'hero.lead' => 'Тест <script>alert(1)</script> и & знак',
    'top.link.01' => 'https://example.org/help',
    'seo.title' => 'CELIKOM <новый> тест',
    'seo.description' => 'Коротко & понятно <script>',
    'media.popup.alt' => 'Новая подпись "интерфейса"',
]);
ensure(str_contains($rendered, '<h1>Знакомые песни<br/><span>И снова вместе!</span></h1>'), 'H1 node structure changed');
ensure(str_contains($rendered, 'Тест &lt;script&gt;alert(1)&lt;/script&gt; и &amp; знак'), 'XSS escaping missing');
ensure(!str_contains($rendered, '<script>alert(1)</script>'), 'Unsafe script rendered');
ensure(str_contains($rendered, '<title>CELIKOM &lt;новый&gt; тест</title>'), 'Title escaping missing');
ensure(str_contains($rendered, 'content="Коротко &amp; понятно &lt;script&gt;" name="description"'), 'SEO description escaping missing');
ensure(str_contains($rendered, 'alt="Новая подпись &quot;интерфейса&quot;" data-managed-media='), 'Popup alt escaping missing');
ensure(str_contains($rendered, 'class="btn primary" href="https://example.org/help"'), 'Link not applied to right element');
ensure(str_contains($rendered, 'class="faq-item"'), 'FAQ markup missing');
ensure(substr_count($rendered, '<details') === 28, 'FAQ count changed');
ensure(str_contains($rendered, '<link rel="stylesheet" href="/assets/css/v10/04-v10.css"/>'), 'v10 CSS missing');
ensure(str_contains($rendered, 'data-managed-media="celikom.popup.approved"'), 'Popup media placeholder was lost');

refuses(static fn() => V10Renderer::render($template, $schema, ['unknown.field' => 'X']), 'Unknown key');
refuses(static fn() => V10Renderer::render($template, $schema, ['media.popup.approved' => 'https://evil.invalid/evil.svg']), 'Direct media injection');
refuses(static fn() => V10Renderer::render($template, $schema, ['seo.description' => '']), 'Empty SEO description');
refuses(static fn() => V10Renderer::render($template, $schema, ['media.popup.alt' => str_repeat('X', 400)]), 'Oversized alt text');
refuses(static fn() => V10Renderer::render($template, $schema, ['top.link.01' => 'javascript:alert(1)']), 'Unsafe scheme');
refuses(static fn() => V10Renderer::render($template, $schema, ['top.link.01' => '//evil.example']), 'Protocol relative URL');
refuses(static fn() => V10Renderer::render($template, $schema, ['hero.eyebrow' => str_repeat('X', 1000)]), 'Oversized text');
refuses(static fn() => V10Renderer::render($template . ' ', $schema), 'Unapproved template mutation');

echo "Stage 3: v10 content manifest (91+13), safe PHP render and default byte parity — PASS\n";
