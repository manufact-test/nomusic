<?php
declare(strict_types=1);
/** Offline renderer for automated visual interaction review; never deployed. */
require dirname(__DIR__).'/app/bootstrap.php';
$template=file_get_contents(dirname(__DIR__).'/app/Templates/site-v10.html');
$manifest=file_get_contents(dirname(__DIR__).'/app/Config/content-fields-v10.json');
$seed=file_get_contents(dirname(__DIR__).'/database/seeds/faq-v10.json');
if (!is_string($template)||!is_string($manifest)||!is_string($seed)) {
 throw new RuntimeException('Missing approved v10 reference');
}
$rendered=\Celikom\Website\CmsEditor::validate($template,$manifest,$seed,['content'=>[],'faq'=>[]]);
echo \Celikom\Website\CmsV10OwnerMotion::apply($rendered);
