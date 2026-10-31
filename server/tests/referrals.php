<?php
declare(strict_types=1);
require __DIR__.'/smoke.php';
use Celikom\Application;
use Celikom\Auth\AuthService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Referral\ReferralService;
$config=require dirname(__DIR__).'/config/app.php';
if (!str_starts_with((string)$config['db_name'],'celikom_test')) throw new RuntimeException('disposable_referral_test_only');
$pdo=Connection::open($config);
(new MigrationRunner($pdo,dirname(__DIR__).'/migrations'))->run();
$before=$pdo->query('SELECT id,status,password_hash FROM users ORDER BY id')->fetchAll();
$catalog=$pdo->query('SELECT id,status,is_active,version FROM track_replacements ORDER BY id')->fetchAll();
$config['auth_enabled']=true;$config['referrals_enabled']=true;$config['environment']='test';
$config['mail_code_pepper']=str_repeat('test-referral-pepper-',3);
$config['mail_test_sink']=static function(string $to,string $message,string $purpose):void {};
$service=new ReferralService($pdo);$ids=[];
function referralReject(callable $call,string $reason):void {
    try {$call();throw new RuntimeException('Expected '.$reason);}
    catch(DomainException $error){expect($error->getMessage()===$reason,'Exact referral rejection');}
}
try {
    foreach([1,2] as $index) {
        $pdo->prepare('INSERT INTO users(email,password_hash) VALUES(?,?)')->execute(['referral-'.bin2hex(random_bytes(12)).'@example.invalid','not-a-real-login']);
        $ids[$index]=(int)$pdo->lastInsertId();
        $pdo->prepare('INSERT INTO user_email_security(user_id,verified_at) VALUES(?,UTC_TIMESTAMP(6))')->execute([$ids[$index]]);
    }
    run('Stage12 reading invitations creates no code or access',function()use($service,$ids,$pdo):void{
        $summary=$service->summary($ids[1]);expect($summary['code']===null,'GET is read-only');
        expect($summary['qualified_count']===0 && !$summary['discount_active'] && !$summary['reward_available'],'No unearned reward');
        expect(!(new Celikom\Entitlement\EntitlementService($pdo))->check($ids[1])->allowed,'No access grant');
    });
    run('Stage12 concurrent independent devices share one immutable account code',function()use($service,$pdo,$ids):void{
        $workers=[];
        for($i=0;$i<3;$i++) {
            $pipes=[];$process=proc_open([PHP_BINARY,__DIR__.'/referral-code-worker.php',(string)$ids[1]],
                [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
            expect(is_resource($process),'Worker started');fclose($pipes[0]);$workers[]=[$process,$pipes];
        }
        $codes=[];foreach($workers as [$process,$pipes]) {
            $codes[]=stream_get_contents($pipes[1]);$error=stream_get_contents($pipes[2]);fclose($pipes[1]);fclose($pipes[2]);
            expect(proc_close($process)===0 && $error==='','Code issuer race succeeds');
        }
        expect(count(array_unique($codes))===1 && preg_match('/^[A-F0-9]{32}$/D',$codes[0])===1,'Stable CSPRNG account code');
        expect($service->code($ids[1])===$codes[0],'Reinstall does not rotate code');
    });
    $code=$service->code($ids[1]);$other=$service->code($ids[2]);
    $input=['email'=>'invited-'.bin2hex(random_bytes(12)).'@example.invalid','password'=>'fixture secure password over twelve',
        'installation_id'=>'8de936d6-2af5-4ca7-973f-24cb5d355777','referral_code'=>strtolower($code),'qualified'=>true];
    run('Stage12 registration atomically binds invitation; client qualification ignored',function()use($pdo,$config,$input,$service,$ids,&$newUser):void{
        $result=(new AuthService($pdo,$config))->register($input,'referral-fixture');
        expect($result['verification_required'],'Normal email confirmation remains required');
        $q=$pdo->prepare('SELECT id FROM users WHERE email=?');$q->execute([$input['email']]);$newUser=(int)$q->fetchColumn();
        expect($newUser>0 && $service->summary($ids[1])['registered_count']===1,'Single immutable attribution');
        expect($service->summary($ids[1])['qualified_count']===0,'Registration is not paid referral');
    });
    $ids[3]=$newUser;
    run('Stage12 self-referral and second referrer rejected; repeated binding is idempotent',function()use($pdo,$service,$ids,$code,$other):void{
        $pdo->beginTransaction();try {
            referralReject(fn()=>$service->bindRegistration($ids[1],$code),'invalid_referral_code');
            $service->bindRegistration($ids[3],$code);
            referralReject(fn()=>$service->bindRegistration($ids[3],$other),'referral_already_bound');
        } finally {$pdo->rollBack();}
        expect($service->summary($ids[1])['registered_count']===1,'No duplicate attribution');
    });
    run('Stage12 unknown/disabled code never creates a half-registered account',function()use($pdo,$config,$input,$ids):void{
        $copy=array_replace($input,['email'=>'unknown-'.bin2hex(random_bytes(12)).'@example.invalid','referral_code'=>str_repeat('F',32)]);
        referralReject(fn()=>(new AuthService($pdo,$config))->register($copy,'referral-fixture'),'invalid_referral_code');
        $q=$pdo->prepare('SELECT COUNT(*) FROM users WHERE email=?');$q->execute([$copy['email']]);expect((int)$q->fetchColumn()===0,'Validation precedes registration');
        $off=$config;$off['referrals_enabled']=false;
        referralReject(fn()=>(new AuthService($pdo,$off))->register($copy,'referral-fixture'),'referrals_disabled');
    });
    run('Stage12 API is bearer-scoped, default-off and cannot accept qualification claims',function()use($pdo,$config,$ids,$code):void{
        $off=$config;$off['referrals_enabled']=false;
        expect((new Application($off))->handle('GET','/api/v1/referrals')->status===404,'Gate off');
        $app=new Application($config);expect($app->handle('GET','/api/v1/referrals')->status===401,'Session required');
        $pdo->prepare('INSERT INTO user_devices(user_id,installation_id) VALUES(?,?)')->execute([$ids[1],'8de936d6-2af5-4ca7-973f-24cb5d355778']);
        $device=(int)$pdo->lastInsertId();$token=bin2hex(random_bytes(32));
        $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at)
            VALUES(?,?,?,?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 15 MINUTE),DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 90 DAY))')
            ->execute([$ids[1],$device,hash('sha256',$token),hash('sha256',random_bytes(32))]);
        $headers=['Authorization'=>'Bearer '.$token];
        $response=$app->handle('GET','/api/v1/referrals',query:['user_id'=>(string)$ids[2]],headers:$headers);
        $data=json_decode($response->body,true,32,JSON_THROW_ON_ERROR);
        expect($response->status===200 && $response->headers['Cache-Control']==='no-store' && $data['code']===$code,'Own code only');
        expect(!str_contains($response->body,'example.invalid'),'No invited email list');
        expect($app->handle('POST','/api/v1/referrals/code',headers:$headers,body:'{"qualified":true}')->status===400,'No paid qualification mutation');
        expect($app->handle('POST','/api/v1/referrals/code',headers:$headers,body:'{}')->status===200,'Explicit issuance retry');
        $pdo->prepare('UPDATE user_sessions SET revoked_at=UTC_TIMESTAMP(6) WHERE user_id=?')->execute([$ids[1]]);
        expect($app->handle('GET','/api/v1/referrals',headers:$headers)->status===401,'Logout invalidates access');
    });
} finally {
    foreach($ids as $id) $pdo->prepare('DELETE FROM referrals WHERE referrer_user_id=? OR invited_user_id=?')->execute([$id,$id]);
    foreach($ids as $id) {
        foreach(['referral_codes','user_auth_events','user_sessions','user_devices','user_email_security'] as $table)
            $pdo->prepare('DELETE FROM '.$table.' WHERE user_id=?')->execute([$id]);
        $pdo->prepare('DELETE FROM users WHERE id=?')->execute([$id]);
    }
}
expect($pdo->query('SELECT id,status,password_hash FROM users ORDER BY id')->fetchAll()===$before,'Existing accounts preserved');
expect($pdo->query('SELECT id,status,is_active,version FROM track_replacements ORDER BY id')->fetchAll()===$catalog,'Moderation preserved');
fwrite(STDOUT,"Stage12 invitation attribution PASS; real-payment qualification and rewards remain disabled.\n");
