<?php
declare(strict_types=1);
require dirname(__DIR__) . '/app/bootstrap.php';

use Celikom\Website\FirstScreenDraft;

$base = dirname(__DIR__);
$template = file_get_contents($base . '/app/Templates/site-v10.html');
$manifest = file_get_contents($base . '/app/Config/content-fields-v10.json');
$approvedScript = file_get_contents($base . '/public/assets/js/v10/sound-demo.js');
if (!is_string($template) || !is_string($manifest) || !is_string($approvedScript)) {
    throw new RuntimeException('Missing approved v10 baseline');
}

function checkDemo(bool $condition, string $reason): void {
    if (!$condition) throw new RuntimeException($reason);
}
function demoReject(callable $callback, string $label): void {
    try { $callback(); } catch (InvalidArgumentException|RuntimeException $expected) { return; }
    throw new RuntimeException('Unsafe demo text accepted: ' . $label);
}
$originalRestored = 'Играет знакомая версия — если она доступна';
$originalSourceDecoded = str_replace('\u00a0', "\u{00A0}", $approvedScript);
checkDemo(str_contains($originalSourceDecoded, $originalRestored), 'Restored default diverged from original JS');

checkDemo(FirstScreenDraft::render($template, $manifest, []) === $template, 'Baseline is not identical');
$malicious = '"><img src=x onerror=alert(1)><script>bad()</script>';
$preview = FirstScreenDraft::render($template, $manifest, ['sound.result.restored' => $malicious]);
checkDemo(str_contains($preview, 'data-editorial-service="Звучит версия из плеера"'), 'Canonical default service label absent');
checkDemo(str_contains($preview, 'data-editorial-restored="&quot;&gt;&lt;img src=x onerror=alert(1)&gt;&lt;script&gt;bad()&lt;/script&gt;"'), 'Dangerous restored text improperly escaped');
checkDemo(!str_contains($preview, '<img src=x onerror=alert(1)>'), 'Raw image injection was accepted');
checkDemo(!str_contains($preview, '<script>bad()</script>'), 'Raw inline script injection was accepted');
checkDemo(substr_count($preview, 'demo-editorial-preview.js') === 1, 'Adapter must exist exactly once');

$withoutAttrs = preg_replace(
    '/ data-editorial-service="[^"]*" data-editorial-restored="[^"]*"/u',
    '', $preview, -1, $count
);
checkDemo($withoutAttrs !== null && $count === 1, 'Expected one trusted pair of data attributes');
$restoredOriginal = str_replace('<script src="/assets/js/v10/demo-editorial-preview.js"></script>', '', $withoutAttrs);
$restoredOriginal = str_replace('<link rel="stylesheet" href="/assets/css/v10/editor-copy-safety.css"/>', '', $restoredOriginal);
checkDemo($restoredOriginal === $template, 'Dynamic-only draft unexpectedly modified v10 HTML');

$emoji = FirstScreenDraft::render($template, $manifest, ['sound.result.restored' => 'Тест 🎵 — версия доступна']);
checkDemo(str_contains($emoji, 'data-editorial-restored="Тест 🎵 — версия доступна"'), 'Unicode text was corrupted');
demoReject(static fn() => FirstScreenDraft::render($template, $manifest, ['sound.result.restored' => "\xC3\x28"]), 'Invalid UTF-8');
demoReject(static fn() => FirstScreenDraft::render($template, $manifest, ['sound.result.restored' => "bad\nline"]), 'Control character');
demoReject(static fn() => FirstScreenDraft::render($template, $manifest, ['sound.result.restored' => '  ']), 'Whitespace only');
demoReject(static fn() => FirstScreenDraft::render($template, $manifest, ['sound.result.restored' => str_repeat('Ж', 121)]), 'Excess Cyrillic length');

echo "Stage 4: demo adapter/approved-default parity, HTML-attribute escaping and invalid data rejection — PASS\n";
