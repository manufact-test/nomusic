<?php

declare(strict_types=1);

require __DIR__ . '/smoke.php';

use Celikom\Admin\AdminAuth;
use Celikom\Admin\ModerationService;
use Celikom\Application;
use Celikom\Application\TrackRequestService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Repositories\PdoCatalogRepository;
use Celikom\Storage\LocalStorageAdapter;

$config = require dirname(__DIR__) . '/config/app.php';
if (!str_starts_with((string) $config['db_name'], 'celikom_test')) {
    if (getenv('CI')) throw new RuntimeException('Admin tests require disposable celikom_test* database');
    exit(0);
}
$pdo = Connection::open($config);
(new MigrationRunner($pdo, dirname(__DIR__) . '/migrations'))->run();
$storage = new LocalStorageAdapter($config['storage_path']);
$config['admin_enabled'] = true;
$pass = 'test-' . bin2hex(random_bytes(16));
$login = 'stage8-' . substr(bin2hex(random_bytes(8)), 0, 10);
$pdo->prepare("INSERT INTO admins (login,password_hash,role) VALUES (?,?,'owner')")
    ->execute([$login,password_hash($pass,PASSWORD_DEFAULT)]);
$adminId=(int)$pdo->lastInsertId();
$auth=new AdminAuth($pdo);
$app = new Application($config);
$formHeaders=['Content-Type'=>'application/x-www-form-urlencoded'];

run('Stage 8 admin: unauthorized routes never expose queues, cookies or private audio', function() use($app):void{
    expect($app->handle('GET','/admin')->status===303,'Anonymous redirected');
    expect($app->handle('GET','/admin/audio/1')->status===403,'No private playback without session');
});
run('Stage 8 admin: disabled gate conceals entire admin surface',function()use($config):void{
    $config['admin_enabled']=false;
    expect((new Application($config))->handle('GET','/admin')->status===404,'Default-off route');
});
$loginGet=$app->handle('GET','/admin/login');
expect($loginGet->status===200,'Login screen');
preg_match('/name="csrf" value="([a-f0-9]{64})"/',$loginGet->body,$match);
$loginNonce=$match[1]??'';
expect(strlen($loginNonce)===64,'Login challenge generated');
$loginCookie=explode(';',$loginGet->headers['Set-Cookie'])[0];
$loginHeaders=$formHeaders+['Cookie'=>$loginCookie];
$loginBody=http_build_query(['login'=>$login,'password'=>$pass,'csrf'=>$loginNonce]);
run('Stage 8 login: CSRF and wrong credentials rejected', function()use($app,$loginHeaders,$loginBody):void{
    expect($app->handle('POST','/admin/login',headers:$loginHeaders,body:'login=wrong&password=foo')->status===403,'Login CSRF');
    expect($app->handle('POST','/admin/login',headers:$loginHeaders,
        body:str_replace('password=', 'password=bad-', $loginBody))->status===401,'Wrong password');
});
$ok=$app->handle('POST','/admin/login',headers:$loginHeaders,body:$loginBody);
expect($ok->status===303,'Login success');
expect(str_contains($ok->headers['Set-Cookie'],'Secure; HttpOnly; SameSite=Strict'),'Secure cookie');
$sessionCookie=explode(';',$ok->headers['Set-Cookie'])[0];
$sessionHeaders=['Cookie'=>$sessionCookie];
$page=$app->handle('GET','/admin',headers:$sessionHeaders);
expect($page->status===200 && str_contains($page->body,'Предложить песню'),'Two queues visible');
$token=AdminAuth::readCookie(['cookie'=>$sessionCookie],AdminAuth::COOKIE);
$csrf=AdminAuth::csrfForToken($token);
$actionHeaders=$formHeaders+$sessionHeaders;
run('Stage 8 CSRF rejection and private preview require authenticated session',function()use($app,$actionHeaders):void{
    expect($app->handle('POST','/admin/action',headers:$actionHeaders,body:'kind=replacement&id=1&action=approve')->status===403,'CSRF');
    expect($app->handle('GET','/admin/audio/123456789')->status===403,'Anonymous preview');
});
$track='891' . substr(bin2hex(random_bytes(3)),0,5);
$path=sys_get_temp_dir().'/celikom-stage8-test-'.bin2hex(random_bytes(8)).'.mp3';
$frame=hex2bin('fffb9064').str_repeat("\0",413);
file_put_contents($path,str_repeat($frame,100));
$hash=hash_file('sha256',$path);
$key='audio/stage8-'.substr($hash,0,30).'.mp3';
$stream=fopen($path,'rb');
$storage->put($key,$stream);fclose($stream);
$pdo->prepare('INSERT INTO tracks(service,service_track_id,artist,title,duration_ms)
    VALUES(?,?,?,?,?)')->execute(['yandex',$track,'Stage8','Synthetic',2612]);
$trackId=(int)$pdo->lastInsertId();
$pdo->prepare('INSERT INTO audio_assets(storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms)
    VALUES(?,?,?,?,?,?)')->execute(['local',$key,$hash,'audio/mpeg',filesize($path),2612]);
$assetId=(int)$pdo->lastInsertId();
$pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active)
    VALUES(?,?,'pending',0)")->execute([$trackId,$assetId]);
$candidate=(int)$pdo->lastInsertId();
$catalog=new PdoCatalogRepository($pdo);
$mod=new ModerationService($pdo,$storage);
try{
    run('Stage 8 pending is not publicly resolvable',function()use($catalog,$track):void{
        expect($catalog->findActive('yandex',$track)===null,'Pending remains hidden');
    });
    run('Stage 8 admin audio: only session may stream pending with Range',function()use($app,$candidate,$sessionHeaders):void{
        $resp=$app->handle('GET','/admin/audio/'.$candidate,headers:$sessionHeaders+['Range'=>'bytes=0-3']);
        expect($resp->status===206 && bytes($resp)===hex2bin('fffb9064'),'Private Range playback');
        expect(($resp->headers['Cache-Control']??'')==='private, no-store','No caching');
        expect($app->handle('GET','/api/v1/audio/'.$candidate)->status===404,'Public audio denied');
    });
    run('Stage 8 approval requires explicit rights check and documented reason',function()use($mod,$adminId,$candidate):void{
        try{$mod->replacement($adminId,$candidate,'approve','reviewed',0,false);
            throw new RuntimeException('No rights gate');}
        catch(DomainException $e){expect($e->getMessage()==='approval_requires_rights_and_reason','Rights gate');}
    });
    run('Stage 8 approve and concurrent/stale form are serialized',function()use($mod,$adminId,$candidate,$catalog,$track):void{
        $mod->replacement($adminId,$candidate,'approve','rights and sound checked',0,true);
        expect((int)$catalog->findActive('yandex',$track)['replacement_id']===$candidate,'Explicit approve resolves');
        try{$mod->replacement($adminId,$candidate,'approve','second review',0,true);
            throw new RuntimeException('Stale approval succeeded');}
        catch(DomainException $e){expect($e->getMessage()==='stale_moderation_form','Stale form guarded');}
    });
    run('Stage 8 disable instantly removes resolved version',function()use($mod,$adminId,$candidate,$catalog,$track):void{
        $mod->replacement($adminId,$candidate,'disable','rights withdrawn',$candidate,false);
        expect($catalog->findActive('yandex',$track)===null,'Disable removes public mapping');
    });
    $otherTrack=$track.'7';
    $pdo->prepare('INSERT INTO tracks(service,service_track_id,artist,title,duration_ms) VALUES(?,?,?,?,?)')
        ->execute(['yandex',$otherTrack,'Stage8','Same asset',2612]);
    $otherId=(int)$pdo->lastInsertId();
    $pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active)
        VALUES(?,?,'pending',0)")->execute([$otherId,$assetId]);
    $otherCandidate=(int)$pdo->lastInsertId();
    run('Stage 8 rejected shared-asset mapping cannot destroy another Track asset',function()use($mod,$adminId,$otherCandidate,$storage,$key):void{
        $mod->replacement($adminId,$otherCandidate,'wrong_track','wrong Yandex ID',0,false);
        expect($storage->exists($key),'Shared asset survives');
    });
    $ownerHash=hash('sha256','stage8-request-'.bin2hex(random_bytes(5)));
    $requestId=(new TrackRequestService($pdo))->submit([
        'service'=>'yandex','track_id'=>$track,'artist'=>'Synthetic','title'=>'Stage 8'
    ],$ownerHash)['request_id'];
    run('Stage 8 requested songs are a separate no-MP3 queue',function()use($app,$sessionHeaders,$requestId,$mod,$adminId,$pdo):void{
        $view=$app->handle('GET','/admin',['tab'=>'requests'],$sessionHeaders);
        expect($view->status===200 && str_contains($view->body,'https://music.yandex.ru/track/'),'Canonical Yandex link');
        $mod->trackRequest($adminId,(int)$requestId,'reviewed','legal version search planned');
        $st=$pdo->prepare('SELECT status FROM track_requests WHERE id=?');$st->execute([$requestId]);
        expect($st->fetchColumn()==='reviewed','Request reviewed without audio upload');
    });
    run('Stage 8 all committed admin decisions include audit',function()use($pdo,$adminId):void{
        $q=$pdo->prepare('SELECT COUNT(*) FROM audit_log WHERE admin_id=?');$q->execute([$adminId]);
        expect((int)$q->fetchColumn()>=4,'Audited approved, disabled, rejected and reviewed');
    });
    run('Stage 8 auth logout revokes session immediately',function()use($app,$sessionHeaders,$actionHeaders,$csrf):void{
        $resp=$app->handle('POST','/admin/logout',headers:$actionHeaders,body:http_build_query(['csrf'=>$csrf]));
        expect($resp->status===303,'Logout');
        expect($app->handle('GET','/admin',headers:$sessionHeaders)->status===303,'Token revoked');
    });
    fwrite(STDOUT,"CELIKOM Stage 8 isolated moderation/security passed.\n");
}finally{
    unlink($path);
    $storage->delete($key);
}
