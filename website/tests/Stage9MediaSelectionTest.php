<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';
use Celikom\Website\CmsMediaAssignment;
use Celikom\Website\CmsMediaStore;
use Celikom\Website\CmsRevisions;
use Celikom\Website\CmsConfig;
use Celikom\Website\Database;
use Celikom\Website\CmsEditor;

function selectAssert(bool $ok,string $why):void {
    if(!$ok)throw new RuntimeException('CMS private media: '.$why);
}
function selectReject(callable $callback,string $why):void {
    try{$callback();}catch(InvalidArgumentException|RuntimeException $e){return;}
    throw new RuntimeException('CMS private media allowed unsafe operation: '.$why);
}
$base=dirname(__DIR__);
$pdo=Database::connect(CmsConfig::databaseSettings());
$html=file_get_contents($base.'/app/Templates/site-v10.html');
$manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
$faq=file_get_contents($base.'/database/seeds/faq-v10.json');
if(!is_string($html)||!is_string($manifest)||!is_string($faq))throw new RuntimeException('Canonical assets missing');
$original=CmsRevisions::publishedPage($pdo,$html,$manifest,$faq);
selectAssert(CmsMediaAssignment::get($pdo)===['version'=>0,'asset_id'=>null],'initial selection');
selectAssert(CmsMediaAssignment::privatePage($html,null,'')===$html,'default selection must preserve v10 bytes');
$parent=sys_get_temp_dir().'/celikom-preview-'.bin2hex(random_bytes(8));
$dir=$parent.'/media';
if(!mkdir($parent,0700) || !mkdir($dir,0700))throw new RuntimeException('Cannot create isolated storage');
$png=base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=',true);
if(!is_string($png))throw new RuntimeException('Bad image fixture');
$key=bin2hex(random_bytes(20)).'.png';
$path=$dir.'/'.$key;
file_put_contents($path,$png);
try {
    $pdo->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,' .
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)'
    )->execute(['site-private/'.$key,'preview.png','image/png',hash('sha256',$png),
        1,1,'Превью & <безопасно>',1]);
    $id=(int)$pdo->lastInsertId();
    selectAssert($id>0,'image ID');
    $selection=CmsMediaAssignment::choose($pdo,1,0,$id,$dir,$base.'/public');
    selectAssert($selection===1,'first private selection');
    selectAssert(CmsMediaAssignment::get($pdo)===['version'=>1,'asset_id'=>$id],
        'persisted private selection');
    selectAssert(CmsMediaAssignment::choose($pdo,1,0,null,$dir,$base.'/public')===null,
        'stale selection overwrote owner');
    selectReject(fn()=>CmsMediaAssignment::choose($pdo,1,1,$id+999999,$dir,$base.'/public'),
        'unknown media ID');
    selectAssert(CmsMediaAssignment::get($pdo)['version']===1,'rejected edit changed version');
    $page=CmsEditor::validate($html,$manifest,$faq,[
        'content'=>['media.popup.alt'=>'Редактируемый ALT CMS'],
        'faq'=>[]
    ]);
    $rendered=CmsMediaAssignment::privatePage($page,$id,'Превью & <безопасно>');
    selectAssert(str_contains($rendered,'src="/admin/?view=media&amp;id='.$id.'"'),
        'private thumbnail source missing');
    selectAssert(str_contains($rendered,'alt="Превью &amp; &lt;безопасно&gt;"'),
        'private image ALT is not HTML-escaped');
    selectAssert(!str_contains($rendered,'src="/media/celikom-popup-approved.png"'),
        'private preview still refers to public screenshot');
    selectAssert(substr_count($rendered,'data-managed-media="celikom.popup.approved"')===1,
        'media node duplicated');
    selectAssert(CmsRevisions::publishedPage($pdo,$html,$manifest,$faq)===$original,
        'private selection changed published snapshot');
    selectReject(fn()=>CmsMediaAssignment::privatePage($page,$id,
        '" onerror="alert(1)'), 'malicious attr');
    selectReject(fn()=>CmsMediaAssignment::privatePage(
        str_replace('data-managed-media="celikom.popup.approved"','data-managed-media="evil"',$page),
        $id,'Safe title'
    ),'altered media tag');
    selectAssert(CmsMediaAssignment::choose($pdo,1,1,null,$dir,$base.'/public')===2,
        'original screenshot not restored');
    selectAssert(CmsMediaAssignment::get($pdo)===['version'=>2,'asset_id'=>null],
        'original screenshot selection missing');
    selectAssert(CmsMediaAssignment::privatePage($page,null,'')===$page,
        'unselected asset modified preview');
    selectAssert((int)$pdo->query(
        "SELECT COUNT(*) FROM audit_log WHERE event_name='cms.media.preview.selected'"
    )->fetchColumn()===2,'selection audit missing');
    selectAssert(CmsRevisions::publishedPage($pdo,$html,$manifest,$faq)===$original,
        'restore-original did not preserve published snapshot');
    echo "Stage9: private-only media selection, stale-tab protection, XSS/ID refusal, public snapshot untouched — PASS\n";
} finally {
    $pdo->prepare("DELETE FROM site_settings WHERE setting_key='website.media.popup.pending'")->execute();
    if(isset($id))$pdo->prepare('DELETE FROM media_assets WHERE id=?')->execute([$id]);
    @unlink($path);
    rmdir($dir);rmdir($parent);
}
