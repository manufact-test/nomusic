<?php

declare(strict_types=1);

require __DIR__.'/smoke.php';
use Celikom\Admin\AdminAuth;
use Celikom\Admin\ModerationService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Reward\RewardService;
use Celikom\Reward\RewardPolicyService;
use Celikom\Storage\LocalStorageAdapter;

$config=require dirname(__DIR__).'/config/app.php';
if(!str_starts_with((string)$config['db_name'],'celikom_test')) throw new RuntimeException('disposable_auto_rewards_only');
$pdo=Connection::open($config);$runner=new MigrationRunner($pdo,dirname(__DIR__).'/migrations');$runner->run();
$policy=new RewardPolicyService($pdo);$original=$policy->read();$reward=new RewardService($pdo);
$catalog=$pdo->query('SELECT id,status,is_active,version FROM track_replacements ORDER BY id')->fetchAll();
$access=$pdo->query('SELECT * FROM entitlement_ledger ORDER BY id')->fetchAll();
$storage=new LocalStorageAdapter($config['storage_path']);$users=[];$tracks=[];$assets=[];$replacements=[];$keys=[];
$pdo->prepare("INSERT INTO admins(login,password_hash,role) VALUES(?,?,'owner')")->execute(['auto-'.bin2hex(random_bytes(10)),'not-a-login']);$admin=(int)$pdo->lastInsertId();
$token=bin2hex(random_bytes(32));$csrf=AdminAuth::csrfForToken($token);
$pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES(?,?,?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 1 HOUR))')->execute([hash('sha256',$token),$admin,hash('sha256',$csrf)]);
$headers=['Cookie'=>AdminAuth::COOKIE.'='.$token,'Content-Type'=>'application/x-www-form-urlencoded'];
try {
    for($i=0;$i<2;$i++) {
        $pdo->prepare('INSERT INTO users(email,password_hash) VALUES(?,?)')->execute(['auto-'.bin2hex(random_bytes(12)).'@example.invalid','not-a-login']);$users[]=(int)$pdo->lastInsertId();
        $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES(?,UTC_TIMESTAMP(6))')->execute([$users[$i]]);
    }
    $create=function(int $user)use($pdo,$storage,&$tracks,&$assets,&$replacements,&$keys):int {
        $bytes=random_bytes(32);$hash=hash('sha256',$bytes);$key='audio/auto-'.$hash.'.mp3';$keys[]=$key;
        $stream=fopen('php://temp','w+b');fwrite($stream,$bytes);rewind($stream);$storage->put($key,$stream);fclose($stream);
        $pdo->prepare('INSERT INTO tracks(service,service_track_id,title,duration_ms) VALUES(?,?,?,2612)')->execute(['yandex',(string)random_int(920000000,929999999),'<script>auto</script>']);$tracks[]=(int)$pdo->lastInsertId();
        $pdo->prepare('INSERT INTO audio_assets(storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms) VALUES(?,?,?,?,?,2612)')->execute(['local',$key,$hash,'audio/mpeg',strlen($bytes)]);$assets[]=(int)$pdo->lastInsertId();
        $pdo->prepare('INSERT INTO track_replacements(track_id,audio_asset_id,uploaded_by_user_id) VALUES(?,?,?)')->execute([end($tracks),end($assets),$user]);$replacements[]=(int)$pdo->lastInsertId();return end($replacements);
    };
    $config['admin_enabled']=true;$config['reward_eligibility_enabled']=true;$app=new Celikom\Application($config);
    $settings=['csrf'=>$csrf,'version'=>$policy->read()['version'],'upload_discount_percent'=>3,'max_discount_percent'=>20,'validity_days'=>30];
    run('Automatic reward settings save with three fields, no reason or manual switch',function()use($app,$headers,$settings,$policy):void {
        expect($app->handle('POST','/admin/rewards/policy',headers:$headers,body:http_build_query($settings))->status===303,'Save without reason succeeds');
        expect($policy->read()['enabled']===1,'Saving enables automatic awards');
        expect($app->handle('POST','/admin/rewards/policy',headers:$headers,body:http_build_query($settings))->status===409,'Stale settings cannot overwrite another save');
        expect($app->handle('POST','/admin/rewards/policy',headers:$headers,body:'csrf=bad')->status===403,'CSRF still required');
        $html=$app->handle('GET','/admin',query:['tab'=>'rewards'],headers:$headers)->body;
        expect(str_contains($html,'Изменить') && !str_contains($html,'Причина') && !str_contains($html,'name="enabled"') && !str_contains($html,'max_reward_per_month'),'No redundant controls');
        expect($app->handle('POST','/admin/rewards/action',headers:$headers,body:'action=approve')->status===404,'No second approval route');
    });
    run('Seven approved songs award 21 percent automatically, 20 now and one next month',function()use($create,$users,$pdo,$storage,$reward,$admin):void {
        for($i=0;$i<7;$i++) {
            $id=$create($users[0]);(new ModerationService($pdo,$storage,$reward))->replacement($admin,$id,'approve','isolated song approval',0,true);
        }
        $summary=$reward->summary($users[0]);
        expect($summary['earned_contributions']===7 && $summary['earned_discount_percent']===21,'Every approval earns immediately');
        expect($summary['available_discount_percent']===20 && $summary['carried_discount_percent']===1,'Overflow is preserved, including partial credit');
        $next=$pdo->query("SELECT DATE_ADD(DATE_FORMAT(DATE(DATE_ADD(UTC_TIMESTAMP(),INTERVAL 3 HOUR)),'%Y-%m-01'),INTERVAL 1 MONTH)")->fetchColumn();
        expect($summary['next_available_from']===$next,'Overflow scheduled for next month');
        $q=$pdo->prepare("SELECT COUNT(*) FROM reward_ledger WHERE user_id=? AND status='approved' AND grant_mode='automatic' AND expires_at IS NULL");$q->execute([$users[0]]);
        expect((int)$q->fetchColumn()===7 && !$summary['application_available'] && !$summary['discount_active'],'Credit waits without expiry; payment still unavailable');
        expect($reward->summary($users[1])['earned_discount_percent']===0,'Other user receives nothing');
    });
    run('Waiting and future portions do not expire and old unused balance carries forward',function()use($pdo,$users,$reward):void {
        $q=$pdo->prepare('SELECT a.id,a.available_from FROM reward_allocations a JOIN reward_ledger l ON l.id=a.reward_id WHERE l.user_id=?');$q->execute([$users[0]]);$before=$q->fetchAll(PDO::FETCH_ASSOC);
        $pdo->prepare("UPDATE reward_allocations a JOIN reward_ledger l ON l.id=a.reward_id SET a.available_from=DATE_SUB(a.available_from,INTERVAL 2 MONTH) WHERE l.user_id=?")->execute([$users[0]]);
        expect($reward->summary($users[0])['available_discount_percent']===20 && $reward->summary($users[0])['carried_discount_percent']===1,'Unpaid older credits retained within cap');
        foreach($before as $row) $pdo->prepare('UPDATE reward_allocations SET available_from=? WHERE id=?')->execute([$row['available_from'],$row['id']]);
    });
    run('Song approval, automatic grant, overflow portions and audit roll back together',function()use($create,$users,$pdo,$storage,$reward,$admin):void {
        $id=$create($users[1]);$trigger='auto_reward_test_'.bin2hex(random_bytes(5));
        $pdo->exec("CREATE TRIGGER $trigger BEFORE INSERT ON audit_log FOR EACH ROW BEGIN IF NEW.action='reward_auto_granted' AND NEW.admin_id=$admin THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='auto_reward_rollback'; END IF; END");
        try {try {(new ModerationService($pdo,$storage,$reward))->replacement($admin,$id,'approve','rollback fixture',0,true);throw new RuntimeException('Expected audit failure');}
            catch(PDOException $e){expect(str_contains($e->getMessage(),'auto_reward_rollback'),'Injected automatic grant fault');}}
        finally {$pdo->exec("DROP TRIGGER $trigger");}
        $q=$pdo->prepare('SELECT status FROM track_replacements WHERE id=?');$q->execute([$id]);expect($q->fetchColumn()==='pending','Song remains pending');
        $q=$pdo->prepare('SELECT COUNT(*) FROM reward_ledger WHERE replacement_id=?');$q->execute([$id]);expect((int)$q->fetchColumn()===0,'No orphan reward or allocations');
    });
    run('Concurrent contributions keep the cap and retries never award twice',function()use($create,$users,$pdo,$storage,$reward,$admin,$policy):void {
        $policy->configure($admin,$policy->read()['version'],['enabled'=>1,'upload_discount_percent'=>3,'max_discount_percent'=>5,'max_reward_per_month'=>10000,'validity_days'=>45]);
        $ids=[$create($users[1]),$create($users[1])];
        foreach($ids as $id) (new ModerationService($pdo,$storage))->replacement($admin,$id,'approve','isolated existing approval',0,true);
        $workers=[];
        foreach([$ids[0],$ids[1],$ids[0],$ids[1]] as $id) {
            $pipes=[];$process=proc_open([PHP_BINARY,__DIR__.'/reward-record-worker.php',(string)$id,(string)$admin],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
            expect(is_resource($process),'Worker starts');fclose($pipes[0]);$workers[]=[$process,$pipes];
        }
        foreach($workers as [$process,$pipes]) {$result=stream_get_contents($pipes[1]);$error=stream_get_contents($pipes[2]);fclose($pipes[1]);fclose($pipes[2]);expect(proc_close($process)===0 && $result==='ok' && $error==='','Concurrent grant succeeds');}
        $summary=$reward->summary($users[1]);expect($summary['earned_contributions']===2 && $summary['available_discount_percent']===5 && $summary['carried_discount_percent']===1,'Exactly two rewards, capped five and queued one');
        $q=$pdo->prepare('SELECT SUM(a.discount_percent) FROM reward_allocations a JOIN reward_ledger l ON l.id=a.reward_id WHERE l.user_id=? AND a.available_from<=DATE(DATE_ADD(UTC_TIMESTAMP(),INTERVAL 3 HOUR))');$q->execute([$users[1]]);expect((int)$q->fetchColumn()===5,'No hidden over-allocation');
    });
    run('Saved rule changes affect new awards and keep previous amounts, dates and lifetimes',function()use($pdo,$policy,$admin,$users,$create,$storage,$reward):void {
        $q=$pdo->prepare('SELECT l.id,l.discount_percent,l.policy_version,a.available_from,a.discount_percent AS part,a.validity_days FROM reward_ledger l JOIN reward_allocations a ON a.reward_id=l.id WHERE l.user_id=? ORDER BY a.id');$q->execute([$users[0]]);$before=$q->fetchAll();
        $policy->configure($admin,$policy->read()['version'],['enabled'=>1,'upload_discount_percent'=>4,'max_discount_percent'=>20,'max_reward_per_month'=>10000,'validity_days'=>60]);
        $q->execute([$users[0]]);expect($q->fetchAll()===$before,'Existing credits and waiting lifetimes preserved');
        $id=$create($users[0]);(new ModerationService($pdo,$storage,$reward))->replacement($admin,$id,'approve','new rules fixture',0,true);
        expect($reward->summary($users[0])['earned_discount_percent']===25,'New song gets new four percent');
        $html=(new Celikom\Reward\RewardAdminView($pdo))->render('csrf',1,false,$users[0]);
        expect(str_contains($html,'&lt;script&gt;auto&lt;/script&gt;') && !str_contains($html,'<script>auto</script>'),'Metadata escaped');
        expect(!str_contains($html,'Начислить') && !str_contains($html,'Причина'),'Read-only grant history');
    });
    run('Reward history groups by account, orders newest first and paginates songs independently',function()use($pdo,$users,$create,$storage,$reward,$admin,$config,$headers):void {
        $view=new Celikom\Reward\RewardAdminView($pdo);
        $before=$pdo->query('SELECT * FROM reward_ledger ORDER BY id')->fetchAll();
        $html=$view->render('csrf',1);
        expect(substr_count($html,'<details class="reward-disclosure"')===2 && !str_contains($html,'>Свернуть</a>'),'Account controls are native disclosures, not page navigation');
        $response=(new Celikom\Application(array_replace($config,['admin_enabled'=>true,'reward_eligibility_enabled'=>true])))->handle('GET','/admin',query:['tab'=>'rewards'],headers:$headers);
        $script=(string)file_get_contents(dirname(__DIR__).'/src/Reward/reward-disclosure.js');
        expect($response->status===200 && str_contains($response->headers['Content-Security-Policy'],"script-src 'sha256-".base64_encode(hash('sha256',$script,true))."'"),'Only exact disclosure script allowed by CSP');
        expect(!str_contains($response->headers['Content-Security-Policy'],"script-src 'unsafe-inline'"),'No unrestricted inline script permission');
        expect(substr_count($html,'class="panel reward-account"')===2 && !str_contains($html,'class="reward-card"'),'One compact card per account, no song wall');
        expect(strpos($html,'Аккаунт #'.$users[0].' ·')<strpos($html,'Аккаунт #'.$users[1].' ·'),'Latest contribution account is first');
        expect(str_contains($html,'Учтено песен: 8') && str_contains($html,'<strong>25%</strong>'),'Account totals match earned rewards');
        $unknown=$view->render('csrf',1,false,PHP_INT_MAX);
        expect(!str_contains($unknown,'class="reward-card"'),'Unknown account cannot expand unrelated songs');
        expect($pdo->query('SELECT * FROM reward_ledger ORDER BY id')->fetchAll()===$before,'Grouping is read-only');
        for($i=0;$i<19;$i++) {
            $id=$create($users[1]);(new ModerationService($pdo,$storage,$reward))->replacement($admin,$id,'approve','group pagination fixture',0,true);
        }
        $html=$view->render('csrf',1,false,$users[1]);
        expect(strpos($html,'Аккаунт #'.$users[1].' ·')<strpos($html,'Аккаунт #'.$users[0].' ·'),'New contribution moves its account to top');
        // 2 existing contributions + 19 new songs: bounded detail, exact own scope.
        expect(substr_count($html,'class="reward-card"')===21,'Only selected account songs expand');
        expect(!str_contains($html,'<script>auto</script>') && str_contains($html,'&lt;script&gt;auto&lt;/script&gt;'),'Song metadata remains escaped');
        for($i=0;$i<6;$i++) {
            $id=$create($users[1]);(new ModerationService($pdo,$storage,$reward))->replacement($admin,$id,'approve','song pagination fixture',0,true);
        }
        $first=$view->render('csrf',1,false,$users[1]);$second=$view->render('csrf',1,false,$users[1],2);
        expect(substr_count($first,'class="reward-card"')===25 && substr_count($second,'class="reward-card"')===2,'Large account history uses 25 songs per page');
        expect(str_contains($first,'song_page=2') && str_contains($second,'song_page=1'),'Song navigation preserves selected account');
        $q=$pdo->prepare('SELECT id FROM reward_ledger WHERE user_id=? ORDER BY id DESC');$q->execute([$users[1]]);$ids=$q->fetchAll(PDO::FETCH_COLUMN);
        expect(strpos($first,'<h3>#'.$ids[0].' ·')<strpos($first,'<h3>#'.$ids[1].' ·'),'Newest song is first within account');
    });
    run('Reward account pagination stays compact beyond 25 accounts',function()use($pdo,&$users,$create,$storage,$reward,$admin):void {
        // Cross the 25-account boundary with isolated fixtures; never change real users.
        for($i=0;$i<25;$i++) {
            $pdo->prepare('INSERT INTO users(email,password_hash) VALUES(?,?)')->execute(['group-'.bin2hex(random_bytes(12)).'@example.invalid','not-a-login']);
            $user=(int)$pdo->lastInsertId();$users[]=$user;
            $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES(?,UTC_TIMESTAMP(6))')->execute([$user]);
            $id=$create($user);(new ModerationService($pdo,$storage,$reward))->replacement($admin,$id,'approve','account pagination fixture',0,true);
        }
        $view=new Celikom\Reward\RewardAdminView($pdo);$first=$view->render('csrf',1);$second=$view->render('csrf',2);
        expect(substr_count($first,'class="panel reward-account"')===25 && substr_count($second,'class="panel reward-account"')===2,'Account pages are bounded independently from song pages');
        expect(!str_contains($first,'class="reward-card"') && str_contains($first,'page=2'),'Large list stays collapsed and navigable');
        expect(!str_contains($first,'Аккаунт #'.$users[0].' ·') && str_contains($second,'Аккаунт #'.$users[0].' ·'),'Oldest account appears once on second page');
    });
    run('Restartable automatic migration never resets allocations or configured policy',function()use($pdo,$runner,$policy):void {
        $before=$pdo->query('SELECT * FROM reward_allocations ORDER BY id')->fetchAll();$settings=$policy->read();
        $pdo->exec("DELETE FROM schema_migrations WHERE version='013_automatic_rewards.sql'");$runner->run();
        expect($pdo->query('SELECT * FROM reward_allocations ORDER BY id')->fetchAll()===$before && $policy->read()===$settings,'DDL retry preserves credits');
    });
    run('New reward allocations follow Moscow month rollover without rewriting history',function()use($pdo,$create,$users,$storage,$reward,$admin):void {
        $before=$pdo->query('SELECT * FROM reward_allocations ORDER BY id')->fetchAll(PDO::FETCH_ASSOC);
        $pdo->exec('SET timestamp=1793483400'); // 2026-10-31 21:50 UTC, November in Moscow.
        try {
            $id=$create($users[1]);(new ModerationService($pdo,$storage,$reward))->replacement($admin,$id,'approve','Moscow boundary fixture',0,true);
            $q=$pdo->prepare('SELECT a.available_from FROM reward_allocations a JOIN reward_ledger l ON l.id=a.reward_id WHERE l.replacement_id=? ORDER BY a.part_index');$q->execute([$id]);
            expect($q->fetchColumn()==='2026-11-01','Moscow November chosen while UTC is October');
            foreach($before as $row){$q=$pdo->prepare('SELECT * FROM reward_allocations WHERE id=?');$q->execute([$row['id']]);expect($q->fetch(PDO::FETCH_ASSOC)===$row,'prior allocation immutable');}
        } finally {$pdo->exec('SET timestamp=0');}
    });

} finally {
    if($pdo->inTransaction()) $pdo->rollBack();
    $pdo->prepare('DELETE FROM audit_log WHERE admin_id=?')->execute([$admin]);$pdo->prepare('DELETE FROM admin_sessions WHERE admin_id=?')->execute([$admin]);
    foreach($users as $id) $pdo->prepare('DELETE FROM reward_ledger WHERE user_id=?')->execute([$id]);
    foreach($replacements as $id) $pdo->prepare('DELETE FROM track_replacements WHERE id=?')->execute([$id]);
    foreach($assets as $id) $pdo->prepare('DELETE FROM audio_assets WHERE id=?')->execute([$id]);
    foreach($tracks as $id) $pdo->prepare('DELETE FROM tracks WHERE id=?')->execute([$id]);
    foreach($users as $id) {$pdo->prepare('DELETE FROM user_email_security WHERE user_id=?')->execute([$id]);$pdo->prepare('DELETE FROM users WHERE id=?')->execute([$id]);}
    $pdo->prepare('DELETE FROM admins WHERE id=?')->execute([$admin]);
    $pdo->prepare('UPDATE reward_policy SET enabled=?,upload_discount_percent=?,max_discount_percent=?,max_reward_per_month=?,validity_days=?,version=? WHERE id=1')->execute(array_map(static fn($key)=>$original[$key],['enabled','upload_discount_percent','max_discount_percent','max_reward_per_month','validity_days','version']));
    foreach($keys as $key) $storage->delete($key);
}
expect($policy->read()===$original,'Original policy restored');
expect($pdo->query('SELECT id,status,is_active,version FROM track_replacements ORDER BY id')->fetchAll()===$catalog,'Existing catalog preserved');
expect($pdo->query('SELECT * FROM entitlement_ledger ORDER BY id')->fetchAll()===$access,'Trial and paid access preserved');
fwrite(STDOUT,"Automatic rewards PASS. Credits wait for verified payment; no payment application simulated.\n");
