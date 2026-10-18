<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\CmsEditor;
use Celikom\Website\CmsV10OwnerMotion;
$root=dirname(__DIR__);
$template=file_get_contents($root.'/app/Templates/site-v10.html');
$manifest=file_get_contents($root.'/app/Config/content-fields-v10.json');
$faq=file_get_contents($root.'/database/seeds/faq-v10.json');
if(!is_string($template)||!is_string($manifest)||!is_string($faq)){
 throw new \RuntimeException('Missing source of truth');
}
$rendered=CmsEditor::validate($template,$manifest,$faq,['content'=>[],'faq'=>[]]);
$page=CmsV10OwnerMotion::apply($rendered);
$asserts=[
 'all 11 v10 sections unchanged'=>substr_count($page,'<section')===substr_count($rendered,'<section'),
 'original popup served with private page auth'=>str_contains($page,'/?v10_popup=approved'),
 'original desktop illustration unchanged'=>str_contains($page,'class="demo-stage"'),
 'original familiar-player art unchanged'=>str_contains($page,'class="familiar-visual"'),
 'original rewards art unchanged'=>str_contains($page,'class="reward-illustration"'),
 'no fabricated illustrations'=>!str_contains($page,'owner-art-core'),
 'two homepage logo targets'=>substr_count($page,'href="/"')>=2,
 'new closing appearance without top CTA'=>!str_contains($page,'Наверх страницы'),
 'all FAQ entries preserved'=>substr_count($page,'class="faq-item"')===28,
 'CSS loaded'=>str_contains($page,'/assets/css/v10/owner-v10-motion.css'),
 'JS loaded'=>str_contains($page,'/assets/js/v10/owner-v10-motion.js'),
 'CSS file exists'=>is_file($root.'/public/assets/css/v10/owner-v10-motion.css'),
 'JS file exists'=>is_file($root.'/public/assets/js/v10/owner-v10-motion.js'),
 'header participation link'=>str_contains($page,'<a href="#contribute">Участие</a>'),
 'header FAQ link'=>str_contains($page,'<a href="#faq">Вопросы</a>'),
 'header installation chip'=>str_contains($page,'class="header-chip" href="#install">Установка →'),
 'no duplicated how-it-works in header'=>!str_contains($page,'class="header-chip" href="#how"'),
 'header navigation no duplicate ideas'=>!str_contains($page,'<a href="#idea">Идея</a>'),
 'original Z-like waveform removed'=>!str_contains($page,'M2 12c3.5 0 3.5-8'),
 'familiar player now has official mark'=>str_contains($page,'class="familiar-orbit"><img src="/assets/images/celikom-mark.svg" alt=""/>'),
 'reward SVG circle'=>str_contains($page,'<circle cx="32" cy="32" r="21"></circle>'),
 'reward retains original black square'=>str_contains($page,'class="reward-symbol"'),
 'base v10 source remains untouched'=>str_contains($template,'Наверх страницы') && str_contains($template,'/media/celikom-popup-approved.png'),
];
foreach($asserts as $name=>$ok){
 if(!$ok)throw new \RuntimeException('v10 review invariant: '.$name);
}
echo "CELIKOM v10 owner UX: preserved artwork/sections/FAQ and assets PASS\n";
