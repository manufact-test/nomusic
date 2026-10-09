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
$config['api_enabled'] = true;
$config['test_api_token'] = str_repeat('stage8-test-read-', 3);
$config['analytics_privacy_key'] = str_repeat('stage8-private-hmac-', 3);
$config['audio_signing_key'] = str_repeat('stage8-test-audio-key-', 3);
$config['owner_reports_enabled'] = true;
$config['owner_report_token'] = str_repeat('stage8-only-report-token-', 3);
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
run('Stage 8 roles: viewer may inspect, never mutate or export',function()
    use($app,$pdo,$auth,$formHeaders,$pass,$csrf):void{
    $viewer='stage8viewer-'.bin2hex(random_bytes(4));
    $pdo->prepare("INSERT INTO admins(login,password_hash,role) VALUES (?,?,'viewer')")
        ->execute([$viewer,password_hash($pass,PASSWORD_DEFAULT)]);
    $identity=$auth->login($viewer,$pass,'test-viewer-'.bin2hex(random_bytes(4)));
    expect($identity!==null,'Viewer login');
    $cookie=AdminAuth::COOKIE.'='.$identity['token'];
    $headers=$formHeaders+['Cookie'=>$cookie];
    expect($app->handle('GET','/admin',headers:['Cookie'=>$cookie])->status===200,'Viewer read access');
    $writeBody=http_build_query(['csrf'=>AdminAuth::csrfForToken($identity['token']),
        'kind'=>'replacement','id'=>'1','action'=>'approve','expected_active'=>'0','reason'=>'reviewed']);
    expect($app->handle('POST','/admin/action',headers:$headers,body:$writeBody)->status===403,'Viewer write forbidden');
    expect($app->handle('POST','/admin/export',headers:$headers,body:http_build_query(['csrf'=>AdminAuth::csrfForToken($identity['token'])]))->status===403,'Viewer export forbidden');
    $pdo->prepare('UPDATE admin_sessions SET expires_at=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 SECOND)
        WHERE token_hash=?')->execute([hash('sha256',$identity['token'])]);
    expect($app->handle('GET','/admin',headers:['Cookie'=>$cookie])->status===303,'Expired viewer session');
});
run('Stage 8 login throttle is enforced even with the correct password',function()use($auth,$login,$pass):void{
    $ip='test-bruteforce-'.bin2hex(random_bytes(6));
    for($i=0;$i<9;$i++)$auth->login($login,'wrong-password-'.$i,$ip);
    expect($auth->login($login,$pass,$ip)===null,'Login locked for current window');
});
run('Stage 8 moderation queues: status and page filters never become SQL injection',function()use($app,$sessionHeaders):void{
    foreach(['uploads','requests','reports'] as $tab) {
        foreach(['pending','invalid','pending OR 1=1'] as $status) {
            $response=$app->handle('GET','/admin',['tab'=>$tab,'status'=>$status,'page'=>'2'],$sessionHeaders);
            expect($response->status===200 && str_contains($response->body,'Статус'),'Queue filter renders');
            expect(!str_contains($response->body,'service_unavailable'),'No query injection');
        }
    }
});
run('Stage 8 CSRF rejection and private preview require authenticated session',function()use($app,$actionHeaders):void{
    expect($app->handle('POST','/admin/action',headers:$actionHeaders,body:'kind=replacement&id=1&action=approve')->status===403,'CSRF');
    expect($app->handle('GET','/admin/audio/123456789')->status===403,'Anonymous preview');
});
$track='891' . (string) random_int(10000,99999);
$path=sys_get_temp_dir().'/celikom-stage8-test-'.bin2hex(random_bytes(8)).'.mp3';
$frame=hex2bin('fffb9064').str_repeat("\0",413);
file_put_contents($path,str_repeat($frame,101));
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
    run('Stage 8 redesign: Russian statuses, safe paging and no raw role/metadata clutter',function()
        use($app,$sessionHeaders):void{
        foreach(['uploads','requests','reports','audit'] as $tab) {
            foreach(['10','25','50'] as $size) {
                $resp=$app->handle('GET','/admin',['tab'=>$tab,'per_page'=>$size,'page'=>'1'],$sessionHeaders);
                expect($resp->status===200,'Paged '.$tab.' '.$size.' available');
                expect(str_contains($resp->body,'name="per_page"'),'Per page selector shown');
                expect(str_contains($resp->body,'value="'.$size.'" selected'),'Page size remembered');
                expect(str_contains($resp->body,'Страница 1 из'),'Numeric pager displayed');
                expect(str_contains($resp->body,'CELIKOM'),'Brand present');
            }
        }
        $page=$app->handle('GET','/admin',['tab'=>'uploads','status'=>'pending','per_page'=>'9 OR 1=1'],$sessionHeaders);
        expect($page->status===200 && str_contains($page->body,'25 записей</option>'),
            'Invalid page size falls back safely');
        expect(str_contains($page->body,'На проверке'),'Russian status label');
        expect(!str_contains($page->body,'active: 0'),'Internal status text not exposed');
    });
    run('Stage 8 legacy metadata: only owner, CSRF and exact Track ID can repair missing labels',function()
        use($app,$pdo,$track,$assetId,$sessionHeaders,$actionHeaders,$csrf):void{
        $oldTrack=$track.'55';
        $pdo->prepare('INSERT INTO tracks(service,service_track_id,artist,title,duration_ms)
            VALUES(?,?,?,?,?)')->execute(['yandex',$oldTrack,'','',2612]);
        $trackDbId=(int)$pdo->lastInsertId();
        $pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active)
            VALUES(?,?,'pending',0)")->execute([$trackDbId,$assetId]);
        $view=$app->handle('GET','/admin',['tab'=>'uploads'],$sessionHeaders);
        expect(str_contains($view->body,'Название не указано'),'Unknown labels are explicit');
        expect(str_contains($view->body,'action="/admin/metadata"'),'Owner can correct missing labels');
        $payload=['track'=>(string)$trackDbId,'expected_track_id'=>$oldTrack,
            'artist'=>'Проверенный исполнитель','title'=>'Проверенная песня'];
        expect($app->handle('POST','/admin/metadata',headers:$actionHeaders,
            body:http_build_query($payload))->status===403,'Metadata requires CSRF');
        expect($app->handle('POST','/admin/metadata',headers:$actionHeaders,
            body:http_build_query(array_merge($payload,['csrf'=>$csrf,'expected_track_id'=>'12345'])))->status===409,
            'Cannot relabel wrong Track ID');
        $payload['csrf']=$csrf;
        expect($app->handle('POST','/admin/metadata',headers:$actionHeaders,
            body:http_build_query($payload))->status===303,'Owner may safely repair label');
        $q=$pdo->prepare('SELECT artist,title,service_track_id FROM tracks WHERE id=?');
        $q->execute([$trackDbId]);$row=$q->fetch(PDO::FETCH_ASSOC);
        expect($row['artist']==='Проверенный исполнитель' && $row['title']==='Проверенная песня'
            && $row['service_track_id']===$oldTrack,'Correct label without Track ID mutation');
        $q=$pdo->prepare("SELECT COUNT(*) FROM audit_log WHERE entity_id=? AND action='track_metadata_labeled'");
        $q->execute([$trackDbId]);
        expect((int)$q->fetchColumn()===1,'Metadata change audited once');
        expect($app->handle('POST','/admin/metadata',headers:$actionHeaders,
            body:http_build_query($payload))->status===409,'Complete metadata not overwritable by quick repair');
    });
    run('Stage 8 pending is not publicly resolvable',function()use($catalog,$track):void{
        expect($catalog->findActive('yandex',$track)===null,'Pending remains hidden');
    });

    run('Stage 8 two-step confirmation forms are separate',function()use($app,$sessionHeaders,$candidate):void{
        $view=$app->handle('GET','/admin',['tab'=>'uploads','per_page'=>'50'],$sessionHeaders);
        expect($view->status===200 && str_contains($view->body,'name="review-'.$candidate.'"'),
            'Grouped review choices');
        expect(str_contains($view->body,'name="decision" value="approval"')
            && str_contains($view->body,'name="decision" value="rejection"'),
            'Explicit independent forms');
        expect(str_contains($view->body,'Подтвердить одобрение')
            && str_contains($view->body,'Подтвердить отклонение'),
            'Separate final confirmation steps');
        expect(str_contains($view->body,'select class="reject-category"')
            && str_contains($view->body,'appearance:base-select')
            && str_contains($view->body,'select.reject-category::picker(select)'),
            'Custom browser-native picker CSS is present without JavaScript');
        expect(str_contains($view->body,'<option value="" selected disabled hidden>Выберите причину</option>')
            && str_contains($view->body,'option[hidden]{display:none!important}'),
            'Placeholder is displayed in the closed picker, not as a selectable menu row');
        expect(str_contains($view->body,'.decision-body .reject-category:focus-visible')
            && str_contains($view->body,'box-shadow:inset 0 0 0 1px #278d70'),
            'Rejection picker uses restrained border-only focus');
    });

    run('Stage 8 two-step approval audits optional comments and blocks missing rights',function()
        use($pdo,$track,$assetId,$app,$csrf,$actionHeaders,$sessionHeaders,$catalog):void{
        $trackName=$track.'74';
        $pdo->prepare('INSERT INTO tracks(service,service_track_id,artist,title,duration_ms) VALUES(?,?,?,?,?)')
            ->execute(['yandex',$trackName,'CI','Two step approval',2612]);
        $trackDb=(int)$pdo->lastInsertId();
        $pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active) VALUES(?,?,'pending',0)")
            ->execute([$trackDb,$assetId]);
        $id=(int)$pdo->lastInsertId();
        $payload=['csrf'=>$csrf,'kind'=>'replacement','id'=>(string)$id,'expected_active'=>'0',
            'decision'=>'approval','action'=>'approve','review_note'=>'Комментарий после проверки'];
        expect($app->handle('POST','/admin/action',headers:$actionHeaders,body:http_build_query($payload))->status===409,
            'Checkbox mandatory server-side');
        expect($catalog->findActive('yandex',$trackName)===null,'Not approved until rights confirmed');
        $payload['rights_confirmed']='1';
        expect($app->handle('POST','/admin/action',headers:$actionHeaders,body:http_build_query($payload))->status===303,
            'Final approval accepted');
        expect((int)$catalog->findActive('yandex',$trackName)['replacement_id']===$id,'Activated');
        $card=$app->handle('GET','/admin',['tab'=>'uploads','status'=>'approved'],$sessionHeaders);
        $journal=$app->handle('GET','/admin',['tab'=>'audit'],$sessionHeaders);
        expect(str_contains($card->body,'Комментарий после проверки') && str_contains($journal->body,'Комментарий после проверки'),
            'Comment shown in card and journal');
    });

    run('Stage 8 rejection categories map to existing audited actions',function()
        use($pdo,$track,$assetId,$app,$csrf,$actionHeaders,$sessionHeaders):void{
        foreach ([['duplicate','','replacement_duplicate','Дубликат'],
                  ['bad_quality','Звук с помехами','replacement_bad_quality','Плохое качество'],
                  ['other','Моя отдельная причина','replacement_reject','Другая причина']] as $i=>$case) {
            [$category,$comment,$expectedAction,$label]=$case;
            $trackName=$track.'8'.($i+1);
            $pdo->prepare('INSERT INTO tracks(service,service_track_id,artist,title,duration_ms) VALUES(?,?,?,?,?)')
                ->execute(['yandex',$trackName,'CI','Two step rejection',2612]);
            $dbTrack=(int)$pdo->lastInsertId();
            $pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active) VALUES(?,?,'pending',0)")
                ->execute([$dbTrack,$assetId]);
            $id=(int)$pdo->lastInsertId();
            $form=['csrf'=>$csrf,'kind'=>'replacement','id'=>(string)$id,'expected_active'=>'0',
                'decision'=>'rejection','action'=>'reject','reject_category'=>$category,'review_note'=>$comment];
            if ($category==='other') {
                expect($app->handle('POST','/admin/action',headers:$actionHeaders,
                    body:http_build_query(array_merge($form,['review_note'=>''])))->status===400,
                    'Custom reason cannot be blank');
            }
            expect($app->handle('POST','/admin/action',headers:$actionHeaders,
                body:http_build_query($form))->status===303,'Rejection confirmed');
            $q=$pdo->prepare('SELECT status,is_active FROM track_replacements WHERE id=?');$q->execute([$id]);
            $state=$q->fetch(PDO::FETCH_ASSOC);
            expect($state['status']==='rejected' && (int)$state['is_active']===0,'Not activated');
            $q=$pdo->prepare('SELECT reason FROM audit_log WHERE entity_type=? AND entity_id=? AND action=? ORDER BY id DESC LIMIT 1');
            $q->execute(['track_replacement',$id,$expectedAction]);$reason=$q->fetchColumn();
            expect(is_string($reason) && str_contains($reason,$label)
                && ($comment==='' || str_contains($reason,$comment)),'Saved rejection reason');
        }
        $view=$app->handle('GET','/admin',['tab'=>'uploads','status'=>'rejected'],$sessionHeaders);
        expect(str_contains($view->body,'Моя отдельная причина'),'Reason appears in card');
    });
    run('Stage 8 admin audio: only session may stream pending with Range',function()use($app,$candidate,$sessionHeaders):void{
        $resp=$app->handle('GET','/admin/audio/'.$candidate,headers:$sessionHeaders+['Range'=>'bytes=0-3']);
        expect($resp->status===206 && bytes($resp)===hex2bin('fffb9064'),'Private Range playback');
        expect(($resp->headers['Cache-Control']??'')==='private, no-store','No caching');
        expect(!in_array($app->handle('GET','/api/v1/audio/'.$candidate)->status,[200,206],true),
            'Pending never streams through public audio route');
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
    run('Stage 8: independent clients resolve only the explicitly approved version',function()
        use($config,$track,$candidate):void{
        $peer=new Application($config);
        $readToken=['Authorization'=>'Bearer '.$config['test_api_token']];
        $reply=$peer->handle('GET','/api/v1/resolve',
            ['service'=>'yandex','track_id'=>$track],$readToken);
        $result=json_decode($reply->body,true,flags:JSON_THROW_ON_ERROR);
        expect($reply->status===200 && $result['found']===true
            && (int)$result['replacement_id']===$candidate,'Independent read client sees approval');
    });
    run('Stage 8 report endpoint: authenticated, duplicate-safe, admin-readable and audited',function()
        use($app,$config,$candidate,$sessionHeaders,$actionHeaders,$csrf,$pdo):void{
        $report=['replacement_id'=>$candidate,'category'=>'bad_quality','details'=>'synthetic report',
            'installation_id'=>'00000000-0000-4000-8000-000000000011'];
        $body=json_encode($report,JSON_THROW_ON_ERROR);
        $endpointHeaders=['Content-Type'=>'application/json'];
        expect($app->handle('POST','/api/v1/report',headers:$endpointHeaders,body:$body)->status===401,'Protected intake');
        $readOnly=$endpointHeaders+['Authorization'=>'Bearer '.$config['test_api_token']];
        expect($app->handle('POST','/api/v1/report',headers:$readOnly,body:$body)->status===401,
            'Read-only API token must never authorize report mutations');
        $headers=$endpointHeaders+['Authorization'=>'Bearer '.$config['owner_report_token']];
        $response=$app->handle('POST','/api/v1/report',headers:$headers,body:$body);
        expect($response->status===202,'Report accepted');
        $record=json_decode($response->body,true,flags:JSON_THROW_ON_ERROR);
        expect($record['status']==='pending' && $record['duplicate']===false,'Pending report');
        $again=json_decode($app->handle('POST','/api/v1/report',headers:$headers,body:$body)->body,true);
        expect($again['duplicate']===true && $again['report_id']===$record['report_id'],'No duplicate report');
        $page=$app->handle('GET','/admin',['tab'=>'reports'],$sessionHeaders);
        expect(str_contains($page->body,'synthetic report'),'Admin sees report');
        $form=http_build_query(['csrf'=>$csrf,'kind'=>'report','id'=>$record['report_id'],
            'action'=>'reviewed','reason'=>'checked synthetic report']);
        expect($app->handle('POST','/admin/action',headers:$actionHeaders,body:$form)->status===303,'Admin report reviewed');
        $q=$pdo->prepare('SELECT status FROM reports WHERE id=?');$q->execute([$record['report_id']]);
        expect($q->fetchColumn()==='reviewed','Report reviewed in DB');
    });
    run('Stage 8 concurrent approvals allow exactly one winner under MySQL Track lock',function()
        use($pdo,$adminId,$track,$assetId,$catalog):void{
        $raceTrack=$track.'9';
        $pdo->prepare('INSERT INTO tracks(service,service_track_id,artist,title,duration_ms)
            VALUES(?,?,?,?,?)')->execute(['yandex',$raceTrack,'Stage8','Approval race',2612]);
        $id=(int)$pdo->lastInsertId();
        $pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active)
            VALUES(?,?,'pending',0)")->execute([$id,$assetId]);
        $candidateId=(int)$pdo->lastInsertId();
        $children=[];
        for($i=0;$i<4;$i++){
            $proc=proc_open([PHP_BINARY,__DIR__.'/admin-race-worker.php',
                (string)$adminId,(string)$candidateId],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
            expect(is_resource($proc),'worker spawned');
            fclose($pipes[0]);$children[]=[$proc,$pipes];
        }
        $codes=[];
        foreach($children as [$proc,$pipes]){
            stream_get_contents($pipes[1]);stream_get_contents($pipes[2]);
            fclose($pipes[1]);fclose($pipes[2]);
            $codes[]=proc_close($proc);
        }
        expect(count(array_filter($codes,static fn(int $code):bool=>$code===0))===1,'Exactly one approve');
        expect(count(array_filter($codes,static fn(int $code):bool=>$code===3))===3,'Three stale/conflicting decisions');
        expect((int)$catalog->findActive('yandex',$raceTrack)['replacement_id']===$candidateId,'One public winner');
    });
    run('Stage 8 disable instantly removes resolved version',function()use($mod,$adminId,$candidate,$catalog,$track):void{
        $mod->replacement($adminId,$candidate,'disable','rights withdrawn',$candidate,false);
        expect($catalog->findActive('yandex',$track)===null,'Disable removes public mapping');
    });
    run('Stage 8: independent clients fail open after explicit disable',function()
        use($config,$track):void{
        $peer=new Application($config);
        $reply=$peer->handle('GET','/api/v1/resolve',['service'=>'yandex','track_id'=>$track],
            ['Authorization'=>'Bearer '.$config['test_api_token']]);
        $result=json_decode($reply->body,true,flags:JSON_THROW_ON_ERROR);
        expect($reply->status===200 && $result['found']===false,'No disabled mapping for independent client');
    });
    run('Stage 8 restore requires explicit fresh rights check, then can be disabled again',function()
        use($mod,$adminId,$candidate,$catalog,$track):void{
        try {
            $mod->replacement($adminId,$candidate,'reactivate','not yet revalidated',0,false);
            throw new RuntimeException('Reactivation accepted without renewed rights review');
        } catch (DomainException $e) {
            expect($e->getMessage()==='approval_requires_rights_and_reason','Rights check');
        }
        expect($catalog->findActive('yandex',$track)===null,'Still disabled without review');
        $mod->replacement($adminId,$candidate,'reactivate','license rechecked manually',0,true);
        expect((int)$catalog->findActive('yandex',$track)['replacement_id']===$candidate,'Explicit reactivation');
        $mod->replacement($adminId,$candidate,'disable','private safety rollback',$candidate,false);
        expect($catalog->findActive('yandex',$track)===null,'Safe subsequent disable');
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
    run('Stage 8 requested songs are a separate no-MP3 queue',function()use($app,$sessionHeaders,$requestId,$mod,$adminId,$pdo,$ownerHash,$track):void{
        $view=$app->handle('GET','/admin',['tab'=>'requests'],$sessionHeaders);
        expect($view->status===200 && str_contains($view->body,'https://music.yandex.ru/track/'),'Canonical Yandex link');
        expect(str_contains($view->body,'Уникальных предложений: 1')
            && !str_contains($view->body,$ownerHash),'Private request count without identity leakage');
        $mod->trackRequest($adminId,(int)$requestId,'reviewed','legal version search planned');
        $st=$pdo->prepare('SELECT status FROM track_requests WHERE id=?');$st->execute([$requestId]);
        expect($st->fetchColumn()==='reviewed','Request reviewed without audio upload');
        $retry=(new TrackRequestService($pdo))->submit([
            'service'=>'yandex','track_id'=>$track,'artist'=>'Synthetic','title'=>'Stage 8'
        ],$ownerHash);
        expect($retry['request_id']===$requestId && $retry['status']==='reviewed',
            'Reviewed suggestion stays reviewed on retry');
    });
    run('Stage 8 all committed admin decisions include audit',function()use($pdo,$adminId):void{
        $q=$pdo->prepare('SELECT COUNT(*) FROM audit_log WHERE admin_id=?');$q->execute([$adminId]);
        expect((int)$q->fetchColumn()>=4,'Audited approved, disabled, rejected and reviewed');
    });
    run('Stage 8 operational overview and audited CSV use real data only',function()use($app,$sessionHeaders,$actionHeaders,$csrf,$pdo,$adminId):void{
        $date=gmdate('Y-m-d');
        $overview=$app->handle('GET','/admin',['tab'=>'overview','from'=>$date,'to'=>$date],$sessionHeaders);
        expect($overview->status===200 && str_contains($overview->body,'Операционный обзор'),'Overview ready');
        expect(str_contains($overview->body,'Агрегированные события')
            || str_contains($overview->body,'Нули не подставляются'),'No fabricated metrics');
        expect($app->handle('POST','/admin/export',headers:$actionHeaders,body:'csrf=bad')->status===403,'CSV CSRF required');
        $csv=$app->handle('POST','/admin/export',headers:$actionHeaders,body:http_build_query(['csrf'=>$csrf]));
        expect($csv->status===200 && str_contains($csv->body,'created_at,admin,action'),'Private CSV');
        $q=$pdo->prepare("SELECT COUNT(*) FROM audit_log WHERE admin_id=? AND action='audit_csv_export'");
        $q->execute([$adminId]);
        expect((int)$q->fetchColumn()===1,'Export logged');
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
