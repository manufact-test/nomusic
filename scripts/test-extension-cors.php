<?php
declare(strict_types=1);
require __DIR__ . '/../server/src/Http/Response.php';
require __DIR__ . '/../server/src/Application.php';
use Celikom\Application;
function check(bool $ok, string $message): void {if (!$ok) throw new RuntimeException($message);}
$app=new Application(['allowed_origins'=>['https://music.yandex.ru'],'version'=>'test','environment'=>'test','auth_enabled'=>false,'admin_enabled'=>false]);
$extension='chrome-extension://abcdefghijklmnopabcdefghijklmnop';
foreach (['/api/v1/auth/me','/api/v1/entitlement','/api/v1/resolve','/api/v1/uploads','/api/v1/audio/1'] as $path) {
 $r=$app->handle('OPTIONS',$path,[],['Origin'=>$extension,'Access-Control-Request-Method'=>'GET','Access-Control-Request-Headers'=>'authorization,content-type,range']);
 check($r->status===204,'extension preflight');
 check(($r->headers['Access-Control-Allow-Origin']??'')===$extension,'exact origin');
 check(!isset($r->headers['Access-Control-Allow-Credentials']),'no cookie authority');
 check(($r->headers['Vary']??'')==='Origin','origin cache isolation');
}
foreach (['null','https://untrusted.example','chrome-extension://'.str_repeat('z',32),$extension.'/', $extension.'.evil',"$extension\n"] as $origin) {
 $r=$app->handle('OPTIONS','/api/v1/auth/me',[],['Origin'=>$origin]);
 check(!isset($r->headers['Access-Control-Allow-Origin']),'untrusted origin denied');
}
foreach (['/admin','/admin/api','/api/v10/auth/me'] as $path) {
 $r=$app->handle('OPTIONS',$path,[],['Origin'=>$extension]);check(!isset($r->headers['Access-Control-Allow-Origin']),'non API boundary');
}
foreach (['DELETE','PUT'] as $method) {
 $r=$app->handle($method,'/api/v1/health',[],['Origin'=>$extension]);check(!isset($r->headers['Access-Control-Allow-Origin']),'method boundary');
}
// The existing native Windows audio exceptions remain restricted to signed audio.
foreach (['null','musicapplication://desktop','music-application://desktop','https://desktop.app.music.yandex.net'] as $origin) {
 $r=$app->handle('OPTIONS','/api/v1/audio/1',[],['Origin'=>$origin]);check($r->status===204,'native audio unchanged');
 $r=$app->handle('OPTIONS','/api/v1/auth/me',[],['Origin'=>$origin]);check(!isset($r->headers['Access-Control-Allow-Origin']),'native auth unchanged');
}
$r=$app->handle('GET','/api/v1/auth/me',[],['Origin'=>$extension]);check($r->status===404,'CORS does not enable disabled authentication');
check(($r->headers['Access-Control-Allow-Origin']??'')===$extension,'actual rejection readable');
echo "PASS scoped extension preflight, rejection visibility and unchanged native origin boundaries\n";
