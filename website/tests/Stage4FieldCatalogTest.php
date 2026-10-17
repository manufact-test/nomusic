<?php
declare(strict_types=1);
require dirname(__DIR__) . '/app/bootstrap.php';

use Celikom\Website\FirstScreenFieldCatalog as Catalog;
use Celikom\Website\FirstScreenDraft;

$base = dirname(__DIR__);
$manifest = file_get_contents($base . '/app/Config/content-fields-v10.json');
$template = file_get_contents($base . '/app/Templates/site-v10.html');
if (!is_string($manifest) || !is_string($template)) throw new RuntimeException('Missing approved Stage4 inputs');
$fields = Catalog::fields($manifest);
if (count($fields) !== 27) throw new RuntimeException('Stage4 field count changed: ' . count($fields));
$sections = array_unique(array_column($fields, 'section'));
if ($sections !== ['header','top','sound']) throw new RuntimeException('Unexpected Stage4 editable section group');
foreach ($fields as $key => $field) {
    Catalog::check($key, $field['default'], $field);
    if ($field['section_label'] === '' || $field['label'] === '') {
        throw new RuntimeException('Editor label is not human-readable');
    }
}
if (($fields['sound.result.restored']['type'] ?? '') !== 'demo_state_text') {
    throw new RuntimeException('Dynamic sound result missing');
}
$allowed = FirstScreenDraft::render($template, $manifest, [
    'header.text.02' => 'О проекте CELIKOM',
    'hero.primary.label' => 'Посмотреть демонстрацию',
    'sound.result.restored' => 'Проверенная песня доступна',
]);
if (!str_contains($allowed, 'Проверенная песня доступна')) throw new RuntimeException('Draft did not render');
foreach ([
    'header.text.02' => str_repeat('А', 25),
    'hero.primary.label' => str_repeat('Б', 33),
    'sound.text.04' => str_repeat('В', 25),
    'sound.result.restored' => str_repeat('Г', 121)
] as $key => $bad) {
    try { FirstScreenDraft::render($template, $manifest, [$key => $bad]); }
    catch (InvalidArgumentException $expected) { continue; }
    throw new RuntimeException('Design budget ignored: '.$key);
}
try { FirstScreenDraft::render($template, $manifest, ['seo.title' => 'Hacked']); }
catch (InvalidArgumentException $expected) {
    echo "Stage4 editorial catalog: 27 typed slots, narrow text budgets, dynamic mode, out-of-scope refusal — PASS\n";
    exit(0);
}
throw new RuntimeException('SEO outside catalog was editable');
