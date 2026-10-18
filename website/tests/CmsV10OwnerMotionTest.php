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
 'original popup is protected by private PHP media'=>str_contains($page,'/media/celikom-popup.php'),
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
 'private media PHP exists'=>is_file($root.'/public/media/celikom-popup.php'),
 'JS file exists'=>is_file($root.'/public/assets/js/v10/owner-v10-motion.js'),
 'base v10 source remains untouched'=>str_contains($template,'Наверх страницы'),
];
foreach($asserts as $name=>$ok){
 if(!$ok)throw new \RuntimeException('v10 review invariant: '.$name);
}
echo "CELIKOM v10 owner UX: preserved artwork/sections/FAQ and assets PASS\n";
