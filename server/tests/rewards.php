<?php

declare(strict_types=1);

require __DIR__.'/smoke.php';

use Celikom\Admin\ModerationService;
use Celikom\Application;
use Celikom\Application\UploadService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Reward\RewardService;
use Celikom\Storage\LocalStorageAdapter;

$config=require dirname(__DIR__).'/config/app.php';
if (!str_starts_with((string)$config['db_name'],'celikom_test')) throw new RuntimeException('disposable_reward_test_only');
$pdo=Connection::open($config);
(new MigrationRunner($pdo,dirname(__DIR__).'/migrations'))->run();
$baseline=$pdo->query('SELECT id,status,is_active,version,uploaded_by_user_id FROM track_replacements ORDER BY id')->fetchAll();
$accessBefore=$pdo->query('SELECT * FROM entitlement_ledger ORDER BY id')->fetchAll();
$storage=new LocalStorageAdapter($config['storage_path']);
$reward=new RewardService($pdo);$mod=new ModerationService($pdo,$storage,$reward);
$users=[];$candidates=[];$assets=[];$tracks=[];$paths=[];$keys=[];
$pdo->prepare("INSERT INTO admins(login,password_hash,role) VALUES(?,?,'owner')")
    ->execute(['reward-'.bin2hex(random_bytes(8)),'not-a-login']);
$admin=(int)$pdo->lastInsertId();
try {
    for($i=0;$i<2;$i++) {
        $pdo->prepare('INSERT INTO users(email,password_hash) VALUES(?,?)')->execute(['reward-'.bin2hex(random_bytes(12)).'@example.invalid','not-a-login']);
        $users[]=(int)$pdo->lastInsertId();
        $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES(?,UTC_TIMESTAMP(6))')->execute([$users[$i]]);
    }
    $create=function(?int $user)use($pdo,$storage,&$candidates,&$assets,&$tracks,&$paths,&$keys):int {
        $path=tempnam(sys_get_temp_dir(),'celikom-reward-');$paths[]=$path;
        $frames=str_repeat(hex2bin('fffb9064').str_repeat("\0",413),100);
        file_put_contents($path,"ID3\x04\x00\x00\x00\x00\x00\x10".random_bytes(16).$frames);
        $uuid=bin2hex(random_bytes(4)).'-0000-4000-8000-'.bin2hex(random_bytes(6));
        $fields=['service'=>'yandex','track_id'=>(string)random_int(880000000,889999999),'duration_ms'=>'2612',
            'declaration'=>'1','request_id'=>$uuid,'user_id'=>'99999999','uploaded_by_user_id'=>'99999999'];
        $file=['error'=>UPLOAD_ERR_OK,'tmp_name'=>$path,'name'=>'fixture.mp3','size'=>filesize($path)];
        $upload=new UploadService($pdo,$storage,31457280,static fn(string $p):bool=>is_file($p));
        $result=$upload->upload($fields,$file,hash('sha256',$uuid),$user);
        $id=(int)$result['replacement_id'];$candidates[]=$id;
        $q=$pdo->prepare('SELECT r.track_id,r.audio_asset_id,r.uploaded_by_user_id,a.storage_key FROM track_replacements r JOIN audio_assets a ON a.id=r.audio_asset_id WHERE r.id=?');
        $q->execute([$id]);$row=$q->fetch(PDO::FETCH_ASSOC);
        $tracks[]=(int)$row['track_id'];$assets[]=(int)$row['audio_asset_id'];$keys[]=$row['storage_key'];
        expect(($row['uploaded_by_user_id']===null?null:(int)$row['uploaded_by_user_id'])===$user,'Uploader comes from trusted argument, never multipart fields');
        $retry=$upload->upload($fields,$file,hash('sha256',$uuid),$user);
        expect($retry['replacement_id']===$id,'Retry preserves original ownership');
        return $id;
    };
    $candidate=$create($users[0]);
    run('Stage12 pending upload and spoofed user fields give no reward or access',function()use($reward,$users,$pdo):void {
        expect($reward->summary($users[0])['pending_contributions']===0,'Upload alone is not a reward');
        expect(!(new Celikom\Entitlement\EntitlementService($pdo))->check($users[0])->allowed,'No trial or paid grant');
    });
    run('Stage12 approve, pending reward evidence and audit commit together',function()use($mod,$admin,$candidate,$reward,$users,$pdo):void {
        $mod->replacement($admin,$candidate,'approve','synthetic isolated rights check',0,true);
        $summary=$reward->summary($users[0]);
        expect($summary['pending_contributions']===1 && !$summary['reward_available'] && !$summary['discount_active'] && !$summary['policy_configured'],'Evidence, not an invented discount');
        expect($reward->summary($users[1])['pending_contributions']===0,'Other account gets no credit');
        $q=$pdo->prepare("SELECT COUNT(*) FROM audit_log WHERE admin_id=? AND action='reward_eligibility_recorded'");$q->execute([$admin]);
        expect((int)$q->fetchColumn()===1,'Decision is auditable');
    });
    run('Stage12 retries, disable/reactivate and shared audio never multiply contributions',function()use($pdo,$mod,$reward,$admin,$candidate,$users,&$candidates,&$tracks):void {
        try {$reward->recordApprovedUpload($candidate,$admin);throw new RuntimeException('Expected transaction guard');}
        catch(LogicException $e){expect($e->getMessage()==='reward_requires_moderation_transaction','No independent commit');}
        $pdo->beginTransaction();$reward->recordApprovedUpload($candidate,$admin);$pdo->commit();
        $mod->replacement($admin,$candidate,'disable','isolated disable',$candidate,false);
        $mod->replacement($admin,$candidate,'reactivate','isolated reactivate',0,true);
        $q=$pdo->prepare('SELECT audio_asset_id FROM track_replacements WHERE id=?');$q->execute([$candidate]);$asset=$q->fetchColumn();
        $pdo->prepare('INSERT INTO tracks(service,service_track_id,duration_ms) VALUES(?,?,2612)')->execute(['yandex',(string)random_int(890000000,899999999)]);
        $track=(int)$pdo->lastInsertId();$tracks[]=$track;
        $pdo->prepare("INSERT INTO track_replacements(track_id,audio_asset_id,uploaded_by_user_id) VALUES(?,?,?)")->execute([$track,$asset,$users[1]]);
        $duplicate=(int)$pdo->lastInsertId();$candidates[]=$duplicate;
        $mod->replacement($admin,$duplicate,'approve','duplicate bytes linked to another track',0,true);
        expect($reward->summary($users[0])['pending_contributions']===1 && $reward->summary($users[1])['pending_contributions']===0,'One asset, original contributor only');
    });
    run('Stage12 rejected, duplicate, wrong track, bad quality and anonymous owner upload do not earn rewards',function()use($create,$mod,$admin,$reward,$users):void {
        foreach(['reject','duplicate','wrong_track','bad_quality'] as $action) {
            $id=$create($users[1]);$mod->replacement($admin,$id,$action,'isolated negative decision',0,false);
        }
        $id=$create(null);$mod->replacement($admin,$id,'approve','owner seed has no customer identity',0,true);
        expect($reward->summary($users[1])['pending_contributions']===0,'No reward for unaccepted work or anonymous seeds');
    });
    run('Stage12 a failed moderation audit rolls back catalog, contribution and reward audit',function()use($create,$pdo,$mod,$admin,$reward,$users):void {
        $id=$create($users[1]);
        $trigger='reward_test_'.bin2hex(random_bytes(6));
        $pdo->exec("CREATE TRIGGER $trigger BEFORE INSERT ON audit_log FOR EACH ROW BEGIN IF NEW.action='replacement_approve' AND NEW.admin_id=$admin THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='isolated_reward_rollback'; END IF; END");
        try {
            try {$mod->replacement($admin,$id,'approve','rollback test',0,true);throw new RuntimeException('Expected audit failure');}
            catch(PDOException $e){expect(str_contains($e->getMessage(),'isolated_reward_rollback'),'Injected audit failure');}
        } finally {$pdo->exec("DROP TRIGGER $trigger");}
        $q=$pdo->prepare('SELECT status,is_active FROM track_replacements WHERE id=?');$q->execute([$id]);$row=$q->fetch(PDO::FETCH_ASSOC);
        expect($row['status']==='pending' && (int)$row['is_active']===0,'Catalog rolled back');
        expect($reward->summary($users[1])['pending_contributions']===0,'Contribution rolled back');
        $q=$pdo->prepare("SELECT COUNT(*) FROM audit_log WHERE admin_id=? AND action='reward_eligibility_recorded'");$q->execute([$admin]);
        expect((int)$q->fetchColumn()===1,'No orphan reward audit');
    });
    run('Stage12 reward read API is default-off, session scoped and has no granting action',function()use($config,$pdo,$users):void {
        expect((new Application($config))->handle('GET','/api/v1/rewards')->status===404,'Gate off');
        $config['auth_enabled']=true;$config['reward_eligibility_enabled']=true;
        $app=new Application($config);expect($app->handle('GET','/api/v1/rewards')->status===401,'Session required');
        $pdo->prepare('INSERT INTO user_devices(user_id,installation_id) VALUES(?,?)')->execute([$users[0],'2ae936d6-2af5-4ca7-973f-24cb5d355778']);
        $device=(int)$pdo->lastInsertId();$token=bin2hex(random_bytes(32));
        $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at)
            VALUES(?,?,?,?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 15 MINUTE),DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 90 DAY))')
            ->execute([$users[0],$device,hash('sha256',$token),hash('sha256',random_bytes(32))]);
        $headers=['Authorization'=>'Bearer '.$token];
        $r=$app->handle('GET','/api/v1/rewards',query:['user_id'=>(string)$users[1]],headers:$headers);
        $data=json_decode($r->body,true,32,JSON_THROW_ON_ERROR);
        expect($r->status===200 && $r->headers['Cache-Control']==='no-store' && $data['pending_contributions']===1,'Own aggregate only');
        expect(!str_contains($r->body,'user_id') && !str_contains($r->body,'storage'),'No personal or audio identity exposed');
        expect($app->handle('POST','/api/v1/rewards',headers:$headers,body:'{"approved":true,"discount":100}')->status===405,'No client reward grant');
        $pdo->prepare('UPDATE user_sessions SET revoked_at=UTC_TIMESTAMP(6) WHERE user_id=?')->execute([$users[0]]);
        expect($app->handle('GET','/api/v1/rewards',headers:$headers)->status===401,'Logout invalidates read');
    });
} finally {
    if ($pdo->inTransaction()) $pdo->rollBack();
    $pdo->prepare('DELETE FROM audit_log WHERE admin_id=?')->execute([$admin]);
    foreach($users as $id) $pdo->prepare('DELETE FROM reward_ledger WHERE user_id=?')->execute([$id]);
    foreach($candidates as $id) {
        $pdo->prepare('DELETE FROM upload_submissions WHERE replacement_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM track_replacements WHERE id=?')->execute([$id]);
    }
    foreach($assets as $id) $pdo->prepare('DELETE FROM audio_assets WHERE id=?')->execute([$id]);
    foreach($tracks as $id) $pdo->prepare('DELETE FROM tracks WHERE id=?')->execute([$id]);
    foreach($users as $id) {
        foreach(['user_sessions','user_devices','user_email_security'] as $table) $pdo->prepare('DELETE FROM '.$table.' WHERE user_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM users WHERE id=?')->execute([$id]);
    }
    $pdo->prepare('DELETE FROM admins WHERE id=?')->execute([$admin]);
    foreach($keys as $key) $storage->delete($key);
    foreach($paths as $path) if(is_file($path)) unlink($path);
}
expect($pdo->query('SELECT id,status,is_active,version,uploaded_by_user_id FROM track_replacements ORDER BY id')->fetchAll()===$baseline,'Existing catalog preserved');
expect($pdo->query('SELECT * FROM entitlement_ledger ORDER BY id')->fetchAll()===$accessBefore,'No access or trial changes');
fwrite(STDOUT,"Stage12 contribution evidence PASS; reward amounts, limits and application remain unconfigured/off.\n");
