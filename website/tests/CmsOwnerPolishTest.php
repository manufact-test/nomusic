<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsEditor;
use Celikom\Website\CmsOwnerPolish;

$root=dirname(__DIR__);
$template=file_get_contents($root.'/app/Templates/site-v10.html');
$manifest=file_get_contents($root.'/app/Config/content-fields-v10.json');
$seed=file_get_contents($root.'/database/seeds/faq-v10.json');
if (!is_string($template)||!is_string($manifest)||!is_string($seed)) {
    throw new RuntimeException('Missing immutable v10 source');
}
$validated=CmsEditor::validate($template,$manifest,$seed,['content'=>[],'faq'=>[]]);
if ($validated!==$template) throw new RuntimeException('Original render changed');
$page=CmsOwnerPolish::apply($validated,$root.'/public');
$checks=[
    'missing media is not emitted'=>!str_contains($page,'/media/celikom-popup-approved.png'),
    'no fake interface mockup'=>!str_contains($page,'class="demo-stage"'),
    'brand icon illustration'=>str_contains($page,'class="owner-art-core"'),
    'reward brand illustration'=>str_contains($page,'owner-reward-badge'),
    'CSS additive asset'=>str_contains($page,'/assets/css/v10/owner-polish.css'),
    'JS additive asset'=>str_contains($page,'/assets/js/v10/owner-polish.js'),
    'both brands link home'=>substr_count($page,'href="/"')>=2,
    'odd closing CTA removed'=>!str_contains($page,'Наверх страницы'),
    'all original site sections exist'=>substr_count($page,'<section')===substr_count($template,'<section'),
    'FAQ still present'=>substr_count($page,'class="faq-item"')===28,
    'no pretending to serve unapproved audio'=>!str_contains($page,'/assets/audio/demo-before.mp3'),
    'no changed v10 source'=>str_contains($template,'/media/celikom-popup-approved.png'),
    'css asset available'=>is_file($root.'/public/assets/css/v10/owner-polish.css'),
    'js asset available'=>is_file($root.'/public/assets/js/v10/owner-polish.js'),
];
foreach($checks as $name=>$condition){
 if(!$condition)throw new RuntimeException('Polish check failed: '.$name);
}
$edited=CmsEditor::validate($template,$manifest,$seed,[
 'content'=>['faq.text.02'=>'Проверка оформления'],
 'faq'=>[]
]);
$polished=CmsOwnerPolish::apply($edited,$root.'/public');
if(!str_contains($polished,'Проверка оформления'))throw new RuntimeException('Published copy lost');
if(str_contains($polished,'href="#top"'))throw new RuntimeException('Stale top link');
echo "CELIKOM owner UX polish: HTML and CMS integrity PASS\n";
