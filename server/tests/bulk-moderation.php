<?php

declare(strict_types=1);

require __DIR__ . '/smoke.php';

use Celikom\Admin\AdminAuth;
use Celikom\Admin\BulkModerationService;
use Celikom\Application;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Storage\LocalStorageAdapter;

$config = require dirname(__DIR__) . '/config/app.php';
if (!str_starts_with((string)$config['db_name'],'celikom_test')) {
    throw new RuntimeException('Bulk tests require isolated disposable MySQL');
}
$pdo = Connection::open($config);
(new MigrationRunner($pdo,dirname(__DIR__).'/migrations'))->run();
$storage = new LocalStorageAdapter($config['storage_path']);
$config['admin_enabled'] = true;
$config['api_enabled'] = true;
$config['analytics_privacy_key'] = str_repeat('bulk-ci-privacy-',4);
$config['audio_signing_key'] = str_repeat('bulk-ci-signing-',4);
$app = new Application($config);
$auth = new AdminAuth($pdo);
$pass = 'bulk-ci-'.bin2hex(random_bytes(8));
$login = 'bulkowner-'.bin2hex(random_bytes(5));
$pdo->prepare("INSERT INTO admins(login,password_hash,role) VALUES(?,?,'owner')")
    ->execute([$login,password_hash($pass,PASSWORD_DEFAULT)]);
$ownerId=(int)$pdo->lastInsertId();
$token=$auth->login($login,$pass,'bulk-owner-ci');
expect($token!==null,'Owner session');
$cookie=AdminAuth::COOKIE.'='.$token['token'];
$csrf=AdminAuth::csrfForToken($token['token']);
$post=['Cookie'=>$cookie,'Content-Type'=>'application/x-www-form-urlencoded'];
$get=['Cookie'=>$cookie];

$frame=hex2bin('fffb9064').str_repeat("\0",413);
$audio=str_repeat($frame,101);
$audioPath=sys_get_temp_dir().'/celikom-bulk-'.bin2hex(random_bytes(8)).'.mp3';
file_put_contents($audioPath,$audio);
$key='audio/bulk-ci-'.bin2hex(random_bytes(8)).'.mp3';
$source=fopen($audioPath,'rb');$storage->put($key,$source);fclose($source);
$pdo->prepare('INSERT INTO audio_assets(storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms)
    VALUES(?,?,?,?,?,?)')->execute(['local',$key,hash('sha256',$audio),'audio/mpeg',strlen($audio),2612]);
$asset=(int)$pdo->lastInsertId();

$create = static function(int $sourceId, int $audioAsset) use($pdo):int {
    $pdo->prepare('INSERT INTO tracks(service,service_track_id,artist,title,duration_ms) VALUES(?,?,?,?,?)')
        ->execute(['yandex',(string)$sourceId,'Bulk CI','Test #'.$sourceId,2612]);
    $track=(int)$pdo->lastInsertId();
    $pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active)
        VALUES(?,?,'pending',0)")->execute([$track,$audioAsset]);
    return (int)$pdo->lastInsertId();
};
$ids=[];$base=random_int(100000000,500000000);
for ($i=0;$i<50;$i++) $ids[]=$create($base+$i,$asset);
$selected = static function(array $candidateIds, int $version=1):array {
    $out=[];foreach($candidateIds as $id)$out[$id]=$version.':0';
    return $out;
};
$submit=static function(string $path, array $payload) use($app,$post) {
    return $app->handle('POST',$path,headers:$post,body:http_build_query($payload));
};
$approve = static function(array $choice) use($csrf):array {
    return ['csrf'=>$csrf,'selected'=>$choice,'bulk_action'=>'approve',
        'confirm_batch'=>'1','rights_confirmed'=>'1','review_note'=>'CI reviewed'];
};
$readState=static function(int $id) use($pdo):array {
    $q=$pdo->prepare('SELECT status,is_active,version FROM track_replacements WHERE id=?');
    $q->execute([$id]);return $q->fetch(PDO::FETCH_ASSOC)?:[];
};

run('50 pending render one-page checkboxes and select-all (no default rights)',function()
    use($app,$get,$ids):void {
    $page=$app->handle('GET','/admin',['tab'=>'uploads','status'=>'pending','per_page'=>'50'],$get);
    if ($page->status !== 200 && getenv('BULK_DEBUG_LIVE_MERGE') === '1') {
        try {
            (new \Celikom\Admin\AdminPanel($GLOBALS['pdo'],$GLOBALS['storage'],false,false,$GLOBALS['config']))
                ->handle('GET','/admin',['tab'=>'uploads','status'=>'pending','per_page'=>'50'],['cookie'=>$get['Cookie']],'');
        } catch (\Throwable $error) {
            fwrite(STDERR,"MERGED_ADMIN_DB_DIAG: ".get_class($error).' '.$error->getMessage()."\n");
        }
    }
    expect($page->status===200,'Queue loads');
    expect(substr_count($page->body,'data-bulk-candidate type="checkbox"')===50,'Exactly fifty selectable');
    expect(str_contains($page->body,'Выделить все на странице (50)'),'50 selection control');
    expect(str_contains($page->body,'name="bulk_action" value="delete"'),'Owner deletion control');
    expect(str_contains($page->headers['Content-Security-Policy']??'','sha256-'),'Script integrity CSP');
    if (($out=getenv('BULK_HTML_OUT'))!==false) file_put_contents($out,$page->body);
});
run('Bulk preview is a non-mutating second confirmation with 50 exact Track IDs',function()
    use($submit,$csrf,$ids,$selected,$pdo):void {
    $resp=$submit('/admin/bulk/preview',['csrf'=>$csrf,'bulk_action'=>'approve','selected'=>$selected($ids)]);
    expect($resp->status===200,'Preview available');
    expect(str_contains($resp->body,'Одобрение: 50 версий'),'50 selected');
    expect(substr_count($resp->body,'name="selected[')===50,'Confirmation preserves exact IDs');
    expect(str_contains($resp->body,'name="rights_confirmed"'),'Rights required in final step');
    expect((int)$pdo->query("SELECT COUNT(*) FROM track_replacements WHERE status='approved'")->fetchColumn()===0,
        'Preview never publishes');
});
run('Bulk server rejects missing rights, missing confirmation, wrong CSRF, 51 IDs',function()
    use($submit,$csrf,$ids,$selected,$approve,$pdo):void {
    $all=$approve($selected($ids));
    $noRights=$all;unset($noRights['rights_confirmed']);
    expect($submit('/admin/bulk/execute',$noRights)->status===409,'Rights checked server-side');
    $noConsent=$all;unset($noConsent['confirm_batch']);
    expect($submit('/admin/bulk/execute',$noConsent)->status===400,'Confirm checked server-side');
    $wrongCsrf=$all;$wrongCsrf['csrf']='broken';
    expect($submit('/admin/bulk/execute',$wrongCsrf)->status===403,'CSRF checked');
    $fiftyOne=$all;$fiftyOne['selected'][999999]='1:0';
    expect($submit('/admin/bulk/execute',$fiftyOne)->status===400,'Maximum fifty enforced');
    expect((int)$pdo->query("SELECT COUNT(*) FROM track_replacements WHERE status='approved'")->fetchColumn()===0,
        'No bulk writes without consent');
});
run('Viewer has no write, moderator has no delete, no session cannot edit',function()
    use($pdo,$pass,$auth,$submit,$csrf,$ids,$selected,$app):void {
    foreach(['viewer','moderator'] as $role){
        $name='bulk'. $role .'-'.bin2hex(random_bytes(4));
        $pdo->prepare('INSERT INTO admins(login,password_hash,role) VALUES(?,?,?)')
            ->execute([$name,password_hash($pass,PASSWORD_DEFAULT),$role]);
        $identity=$auth->login($name,$pass,'bulk-role-'.$role);
        expect($identity!==null,'Role login');
        $headers=['Cookie'=>AdminAuth::COOKIE.'='.$identity['token'],'Content-Type'=>'application/x-www-form-urlencoded'];
        $payload=['csrf'=>AdminAuth::csrfForToken($identity['token']),
            'selected'=>$selected([$ids[0]]),'bulk_action'=>'delete'];
        expect($app->handle('POST','/admin/bulk/preview',headers:$headers,body:http_build_query($payload))->status===403,
            'Viewer/moderator cannot delete');
    }
    expect($app->handle('POST','/admin/bulk/execute',headers:['Content-Type'=>'application/x-www-form-urlencoded'],
        body:http_build_query(['csrf'=>$csrf]))->status===303,'Unauthenticated redirected');
});
run('Exactly 50 selected approve with per-record audit and public activation',function()
    use($submit,$approve,$ids,$selected,$pdo,$readState,$app,$get):void {
    $started=microtime(true);
    $reply=$submit('/admin/bulk/execute',$approve($selected($ids)));
    $seconds=microtime(true)-$started;
    expect($reply->status===200,'50 approved');
    expect(str_contains($reply->body,'Обработано: 50'),'No partial claim');
    foreach($ids as $id){
        $row=$readState($id);
        expect($row['status']==='approved' && (int)$row['is_active']===1 && (int)$row['version']===2,
            'Approved and version incremented for '.$id);
        $q=$pdo->prepare("SELECT after_json FROM audit_log WHERE entity_type='track_replacement'
            AND entity_id=? AND action='replacement_approve' ORDER BY id DESC LIMIT 1");
        $q->execute([$id]);$audit=json_decode((string)$q->fetchColumn(),true);
        expect(isset($audit['batch_id']) && strlen($audit['batch_id'])===24,'Per-id batch audit');
    }
    expect((int)$pdo->query("SELECT COUNT(*) FROM track_replacements WHERE status='approved' AND is_active=1")->fetchColumn()===50,
        'Fifty exactly active');
    fwrite(STDOUT,sprintf("MEASURE bulk_approve_50_seconds=%.3f (isolated CI only)\n",$seconds));
});
run('Stale and missing candidate return conflicts while other candidate succeeds',function()
    use($create,$base,$asset,$submit,$approve,$selected,$pdo,$readState):void {
    $first=$create($base+101,$asset);$second=$create($base+102,$asset);
    $pdo->prepare('UPDATE track_replacements SET version=version+1 WHERE id=?')->execute([$first]);
    $result=$submit('/admin/bulk/execute',$approve($selected([$first,$second])));
    expect($result->status===207,'Partial response, not silent 200');
    expect(str_contains($result->body,'Обработано: 1') && str_contains($result->body,'#'.$first),
        'Conflict ID explicitly rendered');
    expect($readState($first)['status']==='pending','Stale row unchanged');
    expect($readState($second)['status']==='approved','Fresh row changed');
});
run('Reject with mandatory category audits every selected ID, repeat rejected is blocked',function()
    use($create,$base,$asset,$submit,$selected,$csrf,$pdo,$readState):void {
    $ids=[$create($base+103,$asset),$create($base+104,$asset)];
    $form=['csrf'=>$csrf,'selected'=>$selected($ids),'bulk_action'=>'reject',
        'confirm_batch'=>'1','reject_category'=>'bad_quality','review_note'=>'Synthetic quality check'];
    $response=$submit('/admin/bulk/execute',$form);
    expect($response->status===200,'Bulk rejected');
    foreach($ids as $id){
        expect($readState($id)['status']==='rejected','Rejected only');
        $q=$pdo->prepare("SELECT action,reason FROM audit_log WHERE entity_id=? ORDER BY id DESC LIMIT 1");
        $q->execute([$id]);$row=$q->fetch(PDO::FETCH_ASSOC);
        expect($row['action']==='replacement_bad_quality' && str_contains($row['reason'],'Плохое качество'),
            'Categorized audit');
    }
    expect($submit('/admin/bulk/execute',$form)->status===409,'Stale rejection blocked');
});
run('Owner bulk deletion preserves shared MP3 and records tombstone',function()
    use($create,$base,$asset,$submit,$csrf,$selected,$pdo,$storage,$key):void {
    $id=$create($base+105,$asset);
    $form=['csrf'=>$csrf,'selected'=>$selected([$id]),'bulk_action'=>'delete',
        'confirm_batch'=>'1','confirm_count'=>'1','review_note'=>'shared fixture'];
    $result=$submit('/admin/bulk/execute',$form);
    expect($result->status===200,'Shared mapping deleted');
    $q=$pdo->prepare('SELECT id FROM track_replacements WHERE id=?');$q->execute([$id]);
    expect($q->fetchColumn()===false,'Mapping is removed');
    expect($storage->exists($key),'Shared file untouched');
    $q=$pdo->prepare('SELECT service_track_id,cleanup_status FROM bulk_moderation_tombstones WHERE replacement_id=?');
    $q->execute([$id]);$row=$q->fetch(PDO::FETCH_ASSOC);
    expect($row['service_track_id']===(string)($base+105) && $row['cleanup_status']==='shared','Tombstone exact Track ID');
});
run('Owner bulk permanent deletion removes only unreferenced private asset',function()
    use($pdo,$storage,$audioPath,$create,$base,$submit,$csrf,$selected,$readState):void {
    $bytes=file_get_contents($audioPath)."\1";
    $key='audio/bulk-single-'.bin2hex(random_bytes(8)).'.mp3';
    $temp=sys_get_temp_dir().'/celikom-bulk-single-'.bin2hex(random_bytes(8));
    file_put_contents($temp,$bytes);
    $stream=fopen($temp,'rb');$storage->put($key,$stream);fclose($stream);unlink($temp);
    $pdo->prepare('INSERT INTO audio_assets(storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms)
        VALUES(?,?,?,?,?,?)')->execute(['local',$key,hash('sha256',$bytes),'audio/mpeg',strlen($bytes),2612]);
    $asset=(int)$pdo->lastInsertId();
    $id=$create($base+106,$asset);
    $form=['csrf'=>$csrf,'selected'=>$selected([$id]),'bulk_action'=>'delete',
        'confirm_batch'=>'1','confirm_count'=>'1'];
    $wrong=$form;$wrong['confirm_count']='7';
    expect($submit('/admin/bulk/execute',$wrong)->status===400,'Destructive count confirmation');
    expect($submit('/admin/bulk/execute',$form)->status===200,'Permanent delete');
    expect($readState($id)===[] && !$storage->exists($key),'Unshared asset cleaned');
    $q=$pdo->prepare('SELECT cleanup_status FROM bulk_moderation_tombstones WHERE replacement_id=?');
    $q->execute([$id]);expect($q->fetchColumn()==='done','Durable cleanup outcome');
});
run('FK-linked upload history cannot be erased, but other IDs in batch proceed',function()
    use($create,$base,$asset,$submit,$csrf,$selected,$pdo,$readState):void {
    $protected=$create($base+107,$asset);$free=$create($base+108,$asset);
    $pdo->prepare('INSERT INTO upload_submissions
       (uploader_hash,request_id,service,service_track_id,sha256,replacement_id)
       VALUES (?,?,?,?,?,?)')->execute([
        hash('sha256','bulk-test-uploader'), '10000000-0000-4000-8000-'.sprintf('%012d',$protected),
        'yandex',(string)($base+107),str_repeat('a',64),$protected
    ]);
    $form=['csrf'=>$csrf,'selected'=>$selected([$protected,$free]),'bulk_action'=>'delete',
        'confirm_batch'=>'1','confirm_count'=>'2'];
    $response=$submit('/admin/bulk/execute',$form);
    expect($response->status===207,'One protected mapping cannot be silently deleted');
    expect($readState($protected)['status']==='pending','Protected history retained');
    expect($readState($free)===[],'Independent mapping deleted');
    expect(str_contains($response->body,'#'.$protected),'Conflict named');
});
fwrite(STDOUT,"CELIKOM bulk moderation MySQL E2E PASS (synthetic, no production writes)\n");
unlink($audioPath);
