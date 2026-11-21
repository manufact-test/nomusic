<?php

declare(strict_types=1);

require __DIR__.'/smoke.php';
use Celikom\Admin\AdminAuth;
use Celikom\Admin\ModerationService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Reward\RewardService;
use Celikom\Reward\RewardPolicyService;
use Celikom\Reward\RewardDecisionService;
use Celikom\Storage\LocalStorageAdapter;

$config=require dirname(__DIR__).'/config/app.php';
if (!str_starts_with((string)$config['db_name'],'celikom_test')) throw new RuntimeException('disposable_reward_policy_test_only');
$pdo=Connection::open($config);$runner=new MigrationRunner($pdo,dirname(__DIR__).'/migrations');$runner->run();
$policy=new RewardPolicyService($pdo);$originalPolicy=$policy->read();
$catalogBefore=$pdo->query('SELECT id,status,is_active,version FROM track_replacements ORDER BY id')->fetchAll();
$accessBefore=$pdo->query('SELECT * FROM entitlement_ledger ORDER BY id')->fetchAll();
$storage=new LocalStorageAdapter($config['storage_path']);$reward=new RewardService($pdo,false);$decisions=new RewardDecisionService($pdo);
$admins=[];$users=[];$credits=[];$assets=[];$tracks=[];$replacements=[];$keys=[];$headers=[];$csrf=[];
function rewardPolicyReject(callable $call,string $reason):void {
    try{$call();throw new RuntimeException('Expected '.$reason);}catch(DomainException $e){expect($e->getMessage()===$reason,'Exact rejection '.$reason);}
}
try {
    foreach(['owner','moderator','viewer'] as $role) {
        $pdo->prepare('INSERT INTO admins(login,password_hash,role) VALUES(?,?,?)')->execute(['policy-'.bin2hex(random_bytes(8)),'not-a-login',$role]);
        $admins[$role]=(int)$pdo->lastInsertId();$token=bin2hex(random_bytes(32));$csrf[$role]=AdminAuth::csrfForToken($token);
        $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES(?,?,?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 1 HOUR))')
            ->execute([hash('sha256',$token),$admins[$role],hash('sha256',$csrf[$role])]);
        $headers[$role]=['Cookie'=>AdminAuth::COOKIE.'='.$token,'Content-Type'=>'application/x-www-form-urlencoded'];
    }
    for($i=0;$i<3;$i++) {
        $pdo->prepare('INSERT INTO users(email,password_hash) VALUES(?,?)')->execute(['policy-'.bin2hex(random_bytes(12)).'@example.invalid','not-a-login']);
        $users[]=(int)$pdo->lastInsertId();$pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES(?,UTC_TIMESTAMP(6))')->execute([$users[$i]]);
    }
    $create=function(int $user)use($pdo,$storage,$reward,$admins,&$credits,&$assets,&$tracks,&$replacements,&$keys):int {
        $bytes=random_bytes(32);$hash=hash('sha256',$bytes);$key='audio/policy-'.$hash.'.mp3';$keys[]=$key;
        $f=fopen('php://temp','w+b');fwrite($f,$bytes);rewind($f);$storage->put($key,$f);fclose($f);
        $pdo->prepare('INSERT INTO tracks(service,service_track_id,title,duration_ms) VALUES(?,?,?,2612)')->execute(['yandex',(string)random_int(900000000,909999999),'<script>fixture</script>']);
        $track=(int)$pdo->lastInsertId();$tracks[]=$track;
        $pdo->prepare('INSERT INTO audio_assets(storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms) VALUES(?,?,?,?,?,2612)')->execute(['local',$key,$hash,'audio/mpeg',strlen($bytes)]);
        $asset=(int)$pdo->lastInsertId();$assets[]=$asset;
        $pdo->prepare('INSERT INTO track_replacements(track_id,audio_asset_id,uploaded_by_user_id) VALUES(?,?,?)')->execute([$track,$asset,$user]);
        $replacement=(int)$pdo->lastInsertId();$replacements[]=$replacement;
        (new ModerationService($pdo,$storage,$reward))->replacement($admins['owner'],$replacement,'approve','isolated approval evidence',0,true);
        $q=$pdo->prepare('SELECT id FROM reward_ledger WHERE replacement_id=?');$q->execute([$replacement]);$id=(int)$q->fetchColumn();expect($id>0,'Contribution exists');$credits[]=$id;
        return $id;
    };
    $a=[$create($users[0]),$create($users[0]),$create($users[0]),$create($users[0]),$create($users[0])];$b=$create($users[1]);
    $values=['enabled'=>1,'upload_discount_percent'=>20,'max_discount_percent'=>30,'max_reward_per_month'=>2,'validity_days'=>30];
    run('Stage12 policy starts disabled, validates economics, owner role and stale revision',function()use($policy,$decisions,$admins,$a,$values):void {
        $version=$policy->read()['version'];expect($policy->read()['enabled']===0,'No seeded rewards');
        rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[0],1,$version,'approve','fixture'),'reward_policy_disabled');
        rewardPolicyReject(fn()=>$policy->configure($admins['moderator'],$version,$values,'fixture'),'reward_owner_required');
        foreach([['upload_discount_percent'=>101],['max_discount_percent'=>10],['max_reward_per_month'=>0],['validity_days'=>0],['upload_discount_percent'=>'20']] as $bad) {
            try {$policy->configure($admins['owner'],$version,array_replace($values,$bad),'fixture');throw new RuntimeException('Invalid policy accepted');}
            catch(InvalidArgumentException $e){expect($e->getMessage()==='invalid_reward_policy','Exact validation');}
        }
        $policy->configure($admins['owner'],$version,$values,'explicit isolated policy');
        rewardPolicyReject(fn()=>$policy->configure($admins['owner'],$version,$values,'stale fixture'),'stale_reward_policy');
    });
    run('Stage12 grants use configured snapshots; stacking and monthly award count are bounded',function()use($pdo,$policy,$decisions,$admins,$a,$reward,$users):void {
        $version=$policy->read()['version'];
        rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[0],1,$version-1,'approve','stale quote'),'stale_reward_policy');
        foreach([$a[0],$a[1]] as $id) $decisions->decide($admins['owner'],$id,1,$version,'approve','configured fixture grant');
        $summary=$reward->summary($users[0]);expect($summary['approved_credits']===2 && $summary['potential_discount_percent']===30,'20 + 20 capped to 30');
        expect(!$summary['reward_available'] && !$summary['application_available'] && !$summary['discount_active'],'No simulated payment or access');
        $q=$pdo->prepare('SELECT discount_percent, TIMESTAMPDIFF(SECOND,granted_at,expires_at) AS seconds FROM reward_ledger WHERE id=?');$q->execute([$a[0]]);$row=$q->fetch(PDO::FETCH_ASSOC);
        expect((int)$row['discount_percent']===20 && (int)$row['seconds']===30*86400,'Amount and lifetime exactly from policy');
        rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[0],1,$version,'approve','duplicate submit'),'stale_reward_decision');
        rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[2],1,$version,'approve','over monthly count'),'reward_monthly_limit');
        $decisions->decide($admins['owner'],$a[0],2,$version,'revoke','owner cancellation');
        expect($reward->summary($users[0])['potential_discount_percent']===20,'Revocation removes credit');
        rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[2],1,$version,'approve','revocation must not bypass limit'),'reward_monthly_limit');
        $decisions->decide($admins['owner'],$a[3],1,$version,'reject','no grant');
        rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[3],2,$version,'approve','rejected reward'),'reward_not_pending');
    });
    run('Stage12 disabled account or replacement cannot earn a pending reward',function()use($pdo,$policy,$decisions,$admins,$a,$users,$replacements):void {
        $version=$policy->read()['version'];
        $pdo->prepare("UPDATE users SET status='disabled' WHERE id=?")->execute([$users[0]]);
        try {rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[4],1,$version,'approve','disabled user'),'reward_contribution_unavailable');}
        finally{$pdo->prepare("UPDATE users SET status='active' WHERE id=?")->execute([$users[0]]);}
        (new ModerationService($pdo,new LocalStorageAdapter((require dirname(__DIR__).'/config/app.php')['storage_path'])))
            ->replacement($admins['owner'],$replacements[4],'disable','unavailable contribution',$replacements[4],false);
        rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[4],1,$version,'approve','disabled audio'),'reward_contribution_unavailable');
    });
    run('Stage12 expiry is effective on reads, cannot be forced early and has an audited transition',function()use($pdo,$policy,$decisions,$admins,$a,$reward,$users):void {
        $version=$policy->read()['version'];
        rewardPolicyReject(fn()=>$decisions->decide($admins['owner'],$a[1],2,$version,'expire','too early'),'reward_not_expired');
        $pdo->prepare('UPDATE reward_ledger SET granted_at=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 2 DAY),expires_at=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 SECOND) WHERE id=?')->execute([$a[1]]);
        expect($reward->summary($users[0])['approved_credits']===0,'Expired credit excluded without a cron or GET mutation');
        $decisions->decide($admins['owner'],$a[1],2,$version,'expire','confirm actual expiry');
    });
    run('Stage12 reward grant and audit roll back together',function()use($pdo,$policy,$decisions,$admins,$b):void {
        $trigger='reward_grant_test_'.bin2hex(random_bytes(6));$admin=$admins['owner'];
        $pdo->exec("CREATE TRIGGER $trigger BEFORE INSERT ON audit_log FOR EACH ROW BEGIN IF NEW.action='reward_approve' AND NEW.admin_id=$admin THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='isolated_reward_grant_rollback'; END IF; END");
        try {
            try {$decisions->decide($admin,$b,1,$policy->read()['version'],'approve','audit fault');throw new RuntimeException('Expected rollback');}
            catch(PDOException $e){expect(str_contains($e->getMessage(),'isolated_reward_grant_rollback'),'Injected fault');}
        } finally{$pdo->exec("DROP TRIGGER $trigger");}
        $q=$pdo->prepare('SELECT status,discount_percent,granted_at,version FROM reward_ledger WHERE id=?');$q->execute([$b]);$row=$q->fetch(PDO::FETCH_ASSOC);
        expect($row['status']==='pending' && $row['discount_percent']===null && $row['granted_at']===null && (int)$row['version']===1,'No orphan grant');
    });
    run('Stage12 administration is owner-only, gated, CSRF protected and escaped',function()use($config,$headers,$csrf,$policy,$admins,$b,$users):void {
        $config['admin_enabled']=true;$config['reward_eligibility_enabled']=true;$app=new Celikom\Application($config);
        $page=$app->handle('GET','/admin',query:['tab'=>'rewards','page'=>'1 OR 1=1','account'=>(string)$users[0]],headers:$headers['owner']);
        expect($page->status===200 && str_contains($page->body,'Настройки') && !str_contains($page->body,'Причина изменения'),'Real rules and contribution queue');
        expect(str_contains($page->body,'&lt;script&gt;fixture&lt;/script&gt;') && !str_contains($page->body,'<script>fixture</script>'),'Metadata escaped');
        foreach(['moderator','viewer'] as $role) {
            expect($app->handle('GET','/admin',query:['tab'=>'rewards'],headers:$headers[$role])->status===403,'No finance read for '.$role);
            expect($app->handle('POST','/admin/rewards/action',headers:$headers[$role],body:'csrf='.$csrf[$role])->status===404,'No finance write for '.$role);
        }
        expect($app->handle('POST','/admin/rewards/action',headers:$headers['owner'],body:'csrf=bad')->status===404,'Manual route removed');
        $off=$config;$off['reward_eligibility_enabled']=false;
        expect((new Celikom\Application($off))->handle('GET','/admin',query:['tab'=>'rewards'],headers:$headers['owner'])->status===404,'No hidden gate bypass');
        $body=http_build_query(['csrf'=>$csrf['owner'],'id'=>$b,'version'=>1,'policy_version'=>$policy->read()['version'],'action'=>'approve','reason'=>'real admin form fixture']);
        expect($app->handle('POST','/admin/rewards/action',headers:$headers['owner'],body:$body)->status===404,'Manual grant removed');
        expect($app->handle('POST','/admin/rewards/action',headers:$headers['owner'],body:$body)->status===404,'Repeat manual form cannot grant');
    });
    run('Stage12 parallel grants cannot exceed a monthly cap of one',function()use($create,$policy,$values,$admins,$decisions,$users,$reward):void {
        $race=[$create($users[2]),$create($users[2])];
        $policy->configure($admins['owner'],$policy->read()['version'],array_replace($values,['max_reward_per_month'=>1]),'isolated race cap');
        $version=$policy->read()['version'];$workers=[];
        foreach($race as $id) {
            $pipes=[];$process=proc_open([PHP_BINARY,__DIR__.'/reward-grant-worker.php',(string)$admins['owner'],(string)$id,(string)$version],
                [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);expect(is_resource($process),'Worker started');fclose($pipes[0]);$workers[]=[$process,$pipes];
        }
        $results=[];foreach($workers as [$process,$pipes]) {
            $results[]=stream_get_contents($pipes[1]);$error=stream_get_contents($pipes[2]);fclose($pipes[1]);fclose($pipes[2]);
            expect(proc_close($process)===0 && $error==='','Concurrent grant completes safely');
        }
        sort($results);expect($results===['limit','ok'] && $reward->summary($users[2])['approved_credits']===1,'Exactly one award');
    });
    run('Stage12 disabling policy prevents new grants while preserving granted snapshots',function()use($pdo,$policy,$values,$admins,$users,$reward):void {
        $q=$pdo->prepare('SELECT discount_percent,expires_at FROM reward_ledger WHERE user_id=? AND granted_at IS NOT NULL ORDER BY id');$q->execute([$users[2]]);$before=$q->fetchAll();
        $policy->configure($admins['owner'],$policy->read()['version'],array_replace($values,['enabled'=>0]),'pause new issuance');
        $q->execute([$users[2]]);expect($q->fetchAll()===$before && !$reward->summary($users[2])['issuance_enabled'],'Existing grant unchanged');
    });
    run('Stage12 migration retry after applied DDL preserves policy and credits',function()use($pdo,$runner,$policy):void {
        $before=$policy->read();$pdo->exec("DELETE FROM schema_migrations WHERE version='012_reward_policy.sql'");$runner->run();
        expect($policy->read()===$before,'Reapplication neither duplicates columns nor resets configured policy');
    });
} finally {
    if($pdo->inTransaction()) $pdo->rollBack();
    foreach($admins as $id) {$pdo->prepare('DELETE FROM audit_log WHERE admin_id=?')->execute([$id]);$pdo->prepare('DELETE FROM admin_sessions WHERE admin_id=?')->execute([$id]);}
    foreach($credits as $id) $pdo->prepare('DELETE FROM reward_ledger WHERE id=?')->execute([$id]);
    foreach($replacements as $id) $pdo->prepare('DELETE FROM track_replacements WHERE id=?')->execute([$id]);
    foreach($assets as $id) $pdo->prepare('DELETE FROM audio_assets WHERE id=?')->execute([$id]);
    foreach($tracks as $id) $pdo->prepare('DELETE FROM tracks WHERE id=?')->execute([$id]);
    foreach($users as $id) {$pdo->prepare('DELETE FROM user_email_security WHERE user_id=?')->execute([$id]);$pdo->prepare('DELETE FROM users WHERE id=?')->execute([$id]);}
    foreach($admins as $id) $pdo->prepare('DELETE FROM admins WHERE id=?')->execute([$id]);
    $pdo->prepare('UPDATE reward_policy SET enabled=?,upload_discount_percent=?,max_discount_percent=?,max_reward_per_month=?,validity_days=?,version=? WHERE id=1')
        ->execute(array_map(static fn($key)=>$originalPolicy[$key],['enabled','upload_discount_percent','max_discount_percent','max_reward_per_month','validity_days','version']));
    foreach($keys as $key) $storage->delete($key);
}
expect($policy->read()===$originalPolicy,'Original policy preserved after isolated tests');
expect($pdo->query('SELECT id,status,is_active,version FROM track_replacements ORDER BY id')->fetchAll()===$catalogBefore,'Existing moderation preserved');
expect($pdo->query('SELECT * FROM entitlement_ledger ORDER BY id')->fetchAll()===$accessBefore,'No trial, paid access or entitlement effects');
fwrite(STDOUT,"Stage12 configured reward policy PASS. Payment application remains unavailable.\n");
