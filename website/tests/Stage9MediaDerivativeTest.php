<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\CmsMediaDerivative;
use Celikom\Website\CmsMediaAssignment;
use Celikom\Website\CmsMediaReleasePreflight;
use Celikom\Website\CmsRevisions;
use Celikom\Website\CmsConfig;
use Celikom\Website\Database;

function derivAssert(bool $passed,string $message):void {
    if(!$passed)throw new RuntimeException('Private derivative: '.$message);
}
function derivReject(callable $task,string $reason):void {
    try{$task();}catch(InvalidArgumentException|RuntimeException $e){return;}
    throw new RuntimeException('Private derivative allowed unsafe operation: '.$reason);
}
if(!extension_loaded('gd'))throw new RuntimeException('GD required for Stage 9 derivative QA');
$base=dirname(__DIR__);
$pdo=Database::connect(CmsConfig::databaseSettings());
$parent=sys_get_temp_dir().'/celikom-derivative-'.bin2hex(random_bytes(10));
$media=$parent.'/media';
$review=$parent.'/review';
if(!mkdir($parent,0700) || !mkdir($media,0700) || !mkdir($review,0700)){
    throw new RuntimeException('Cannot create disposable private directories');
}
$public=$base.'/public';
$path='';
$id=null;
try {
    $source=imagecreatetruecolor(3,2);
    imagealphablending($source,false);
    imagesavealpha($source,true);
    $color=imagecolorallocatealpha($source,40,90,130,50);
    imagefill($source,0,0,$color);
    ob_start();
    imagepng($source);
    $clean=ob_get_clean();
    imagedestroy($source);
    derivAssert(is_string($clean) && strlen($clean)>30,'test PNG unavailable');
    // Insert a valid optional PNG tEXt chunk carrying an identifiable canary.
    $pos=strpos($clean,"IEND");
    derivAssert($pos!==false && $pos>=4,'PNG IEND chunk absent');
    $marker='CANARY-PRIVATE-METADATA-REMOVE-ME';
    $body="Description\0".$marker;
    $type='tEXt';
    $chunk=pack('N',strlen($body)).$type.$body.pack('N',crc32($type.$body));
    $withMetadata=substr($clean,0,$pos-4).$chunk.substr($clean,$pos-4);
    derivAssert(str_contains($withMetadata,$marker) &&
        getimagesizefromstring($withMetadata)!==false,
        'metadata fixture invalid');
    $key=bin2hex(random_bytes(20)).'.png';
    $path=$media.'/'.$key;
    file_put_contents($path,$withMetadata);
    chmod($path,0600);
    $pdo->prepare('INSERT INTO media_assets(storage_key,original_filename,mime_type,sha256,'.
        'pixel_width,pixel_height,alt_text,created_by) VALUES(?,?,?,?,?,?,?,?)')
        ->execute(['site-private/'.$key,'popup.png','image/png',
            hash('sha256',$withMetadata),3,2,'Подтверждение прав отдельно',1]);
    $id=(int)$pdo->lastInsertId();
    derivAssert($id>0,'private fixture media id');
    $template=file_get_contents($base.'/app/Templates/site-v10.html');
    $manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
    $faq=file_get_contents($base.'/database/seeds/faq-v10.json');
    $published=CmsRevisions::publishedPage($pdo,$template,$manifest,$faq);

    derivReject(fn()=>CmsMediaDerivative::preparePending($pdo,$media,$review,$public),
        'unselected original');
    derivAssert(CmsMediaAssignment::choose($pdo,1,0,$id,$media,$public)===1,
        'cannot privately choose PNG');
    derivReject(fn()=>CmsMediaDerivative::preparePending($pdo,$media,$public,$public),
        'destination inside public_html');
    derivReject(fn()=>CmsMediaDerivative::preparePending($pdo,$media,$media,$public),
        'overlapping source and destination');
    chmod($review,0777);
    derivReject(fn()=>CmsMediaDerivative::preparePending($pdo,$media,$review,$public),
        'world writable staging');
    chmod($review,0700);
    derivAssert(glob($review.'/*')===[],'rejected operations created files');

    $result=CmsMediaDerivative::preparePending($pdo,$media,$review,$public);
    derivAssert($result['asset_id']===$id &&
        $result['selection_version']===1 &&
        $result['source_sha256']===hash('sha256',$withMetadata) &&
        $result['public_ready']===false &&
        $result['requires_owner_rights_review']===true &&
        $result['requires_visual_review']===true &&
        $result['mime']==='image/png' &&
        $result['width']===3 && $result['height']===2,
        're-encoded file marked public or metadata mismatch');
    $prepared=$review.'/'.$result['derivative_filename'];
    derivAssert(is_file($prepared) && !is_link($prepared) &&
        (fileperms($prepared)&0777)===0600,
        'prepared derivative must be 0600 regular file');
    $bytes=file_get_contents($prepared);
    derivAssert(is_string($bytes) &&
        !str_contains($bytes,$marker) &&
        hash('sha256',$bytes)===$result['derivative_sha256'] &&
        getimagesizefromstring($bytes)[0]===3 &&
        getimagesizefromstring($bytes)[1]===2 &&
        $bytes!==$withMetadata,
        'derivative did not strip metadata or preserve dimensions');
    derivAssert(CmsMediaAssignment::get($pdo)===['version'=>1,'asset_id'=>$id] &&
        CmsRevisions::publishedPage($pdo,$template,$manifest,$faq)===$published,
        'staging changed CMS selection or published revisions');
    // Corruption of originally verified private media must block staging.
    file_put_contents($path,'altered raw bytes');
    derivReject(fn()=>CmsMediaDerivative::preparePending($pdo,$media,$review,$public),
        'altered source SHA accepted');
    file_put_contents($path,$withMetadata);
    derivAssert(CmsMediaAssignment::choose($pdo,1,1,null,$media,$public)===2,
        'cannot restore original selection');
    derivReject(fn()=>CmsMediaDerivative::preparePending($pdo,$media,$review,$public),
        'original screenshot mistakenly staged');
    derivAssert(!is_file($public.'/'.$result['derivative_filename']),
        'derivative leaked into public webroot');
    echo "Stage9: private PNG re-encoding, metadata removal, 0600, SHA, negative paths, public gate — PASS\n";
} finally {
    $pdo->prepare("DELETE FROM site_settings WHERE setting_key='website.media.popup.pending'")->execute();
    if($id!==null)$pdo->prepare('DELETE FROM media_assets WHERE id=?')->execute([$id]);
    foreach(glob($review.'/*') ?: [] as $entry)@unlink($entry);
    foreach(glob($review.'/.candidate-*') ?: [] as $entry)@unlink($entry);
    if(is_file($path))@unlink($path);
    chmod($review,0700);
    rmdir($review);
    rmdir($media);
    rmdir($parent);
}
