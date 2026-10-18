<?php
declare(strict_types=1);
/**
 * Private v10 original screenshot, served ONLY with staging authentication.
 * No public static PNG, no arbitrary image IDs, no user data disclosure.
 */
header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: private, no-store');
header('X-Content-Type-Options: nosniff');
header('X-Robots-Tag: noindex, nofollow, noarchive');
header('X-Frame-Options: DENY');

$root=dirname(__DIR__,2);
$app=$root.'/celikom-private/app';
if(!is_file($app.'/bootstrap.php')){
    http_response_code(503);
    exit;
}
require $app.'/bootstrap.php';
try{
    if(!\Celikom\Website\CmsStagingGate::approved($app)){
        throw new RuntimeException('Not an approved private staging site');
    }
    \Celikom\Website\CmsStagingHttpAuth::enforce($app);
    $folder=getenv('CELIKOM_SITE_MEDIA_DIR');
    if(!is_string($folder)||$folder===''){
        throw new RuntimeException('Missing private media directory');
    }
    $pdo=\Celikom\Website\Database::connect(\Celikom\Website\CmsConfig::databaseSettings());
    $q=$pdo->prepare("SELECT id FROM media_assets WHERE sha256=? AND mime_type='image/png' AND is_active=1 ORDER BY id DESC LIMIT 1");
    $q->execute(['0366d4f32b0edf67c2300b372202e5604999fa9e9dbb8f2ebfd295aed6fcf1fc']);
    $id=$q->fetchColumn();
    if($id===false){http_response_code(404);exit;}
    $image=\Celikom\Website\CmsMediaStore::privatePreview(
        $pdo,(int)$id,$folder,$root.'/public_html'
    );
    if($image['mime']!=='image/png'){throw new RuntimeException('Unexpected image format');}
    header('Content-Type: image/png');
    header('Content-Length: '.strlen($image['body']));
    echo $image['body'];
}catch(Throwable $e){
    error_log('CELIKOM v10 original protected image unavailable');
    http_response_code(503);
}
