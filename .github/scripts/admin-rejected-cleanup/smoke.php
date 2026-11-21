<?php

declare(strict_types=1);
ini_set('display_errors','0');
function bulkCheck(bool $ok, string $code): void { if (!$ok) throw new RuntimeException($code); }
function bulkHttp(string $path, string $cookie = '', ?array $form = null): array {
    bulkCheck(str_starts_with($path,'/admin') || $path === '/api/v1/config','path');
    $ch = curl_init('https://darkred-camel-588676.hostingersite.com' . $path);
    curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_FOLLOWLOCATION=>false,
        CURLOPT_HTTPHEADER=>['Cache-Control: no-store','Cookie: '.$cookie],CURLOPT_SSL_VERIFYPEER=>true,
        CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>25]);
    if ($form !== null) curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>http_build_query($form)]);
    $body = curl_exec($ch); $code = (int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE); curl_close($ch);
    bulkCheck(is_string($body) && strlen($body) < 4194304,'response'); return [$code,$body];
}
$pdo=null; $session=null;
try {
    bulkCheck(PHP_SAPI==='cli' && $argc===3,'arguments');
    $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release=realpath($argv[1]); $mode=$argv[2];
    bulkCheck(is_string($release) && str_starts_with($release,$root.'/releases/admin-rejected-cleanup-') && in_array($mode,['candidate','active'],true),'release');
    require $release.'/bootstrap.php'; $config=require $release.'/config/app.php';
    $pdo=Celikom\Database\Connection::open($config);
    $pdo->query('SELECT batch_id,replacement_id,service_track_id,cleanup_status FROM bulk_moderation_tombstones LIMIT 0');
    $before=$pdo->query("SELECT COUNT(*) AS n,SUM(version) AS versions,SUM(is_active) AS active,SUM(status='pending') AS pending FROM track_replacements")->fetch(PDO::FETCH_ASSOC);
    $rows=$pdo->query("SELECT r.id,r.version,COALESCE((SELECT a.id FROM track_replacements a WHERE a.track_id=r.track_id AND a.status='approved' AND a.is_active=1 AND a.disabled_at IS NULL LIMIT 1),0) AS active_id,t.service_track_id FROM track_replacements r JOIN tracks t ON t.id=r.track_id WHERE r.status='pending' ORDER BY r.id DESC LIMIT 5")->fetchAll(PDO::FETCH_ASSOC);
    $hasPending=count($rows)>0;
    if(!$hasPending) $rows=$pdo->query("SELECT r.id,r.version,COALESCE((SELECT a.id FROM track_replacements a WHERE a.track_id=r.track_id AND a.status='approved' AND a.is_active=1 AND a.disabled_at IS NULL LIMIT 1),0) AS active_id,t.service_track_id FROM track_replacements r JOIN tracks t ON t.id=r.track_id WHERE r.status='approved' ORDER BY r.id DESC LIMIT 5")->fetchAll(PDO::FETCH_ASSOC);
    bulkCheck(count($rows)>0,'catalog_sample'); $selected=[];
    foreach($rows as $row) $selected[(int)$row['id']]=$row['version'].':'.$row['active_id'];
    $storage=new Celikom\Storage\LocalStorageAdapter($config['storage_path']);
    $panel=new Celikom\Admin\AdminPanel($pdo,$storage,false,false,$config);
    $uploads=new ReflectionMethod($panel,'uploads');
    $html=$uploads->invoke($panel,['role'=>'owner'],'qa-unused',['status'=>'pending','per_page'=>'50']);
    if($hasPending) bulkCheck(substr_count($html,'data-bulk-candidate type="checkbox"')>=count($rows) && str_contains($html,'data-bulk-all') && str_contains($html,'Одобрить выбранные'),'candidate_controls');
    else bulkCheck(!str_contains($html,'data-bulk-candidate') && str_contains($html,'Записей пока нет'),'empty_pending_queue');
    $id=(string)$rows[0]['service_track_id'];
    $search=$uploads->invoke($panel,['role'=>'owner'],'qa-unused',['q'=>$id]);
    bulkCheck(str_contains($search,'Всего: 1 ·') && str_contains($search,'Track ID '.$id.'</div>'),'search');
    $bulk=new Celikom\Admin\BulkModerationService($pdo,$storage);
    try {
        $preview=$bulk->preview(Celikom\Admin\BulkModerationService::selected($selected),'approve','owner');
        bulkCheck($hasPending && count($preview)===count($rows),'preview');
    } catch (DomainException $error) { bulkCheck(!$hasPending && str_starts_with($error->getMessage(),'bulk_stale_candidate_'),'approved_cannot_be_reapproved'); }
    bulkCheck((new ReflectionMethod(Celikom\Admin\ModerationService::class,'replacement'))->getNumberOfParameters()===8,'version_lock');
    $inactiveSamples=[];
    foreach(['rejected','disabled'] as $status) {
        $get=$pdo->prepare("SELECT r.id,r.version,t.service_track_id,COALESCE((SELECT a.id FROM track_replacements a WHERE a.track_id=r.track_id AND a.status='approved' AND a.is_active=1 AND a.disabled_at IS NULL LIMIT 1),0) AS active_id FROM track_replacements r JOIN tracks t ON t.id=r.track_id WHERE r.status=? AND NOT EXISTS(SELECT 1 FROM bulk_moderation_tombstones b WHERE b.replacement_id=r.id) ORDER BY r.id DESC LIMIT 1");
        $get->execute([$status]);$sample=$get->fetch(PDO::FETCH_ASSOC);if(!$sample)continue;
        $inactiveSamples[$status]=$sample;
        $inactiveHtml=$uploads->invoke($panel,['role'=>'owner'],'qa-unused',['status'=>$status,'per_page'=>'50']);
        bulkCheck(str_contains($inactiveHtml,'name="selected['.$sample['id'].']"') && str_contains($inactiveHtml,'data-bulk-status="'.$status.'"'),'inactive_checkbox_'.$status);
        $choice=[(int)$sample['id']=>$sample['version'].':'.$sample['active_id']];
        bulkCheck(count($bulk->preview(Celikom\Admin\BulkModerationService::selected($choice),'delete','owner'))===1,'inactive_preview_'.$status);
    }
    if($mode==='active') {
        bulkCheck(realpath($root.'/current')===$release,'current');
        $owner=$pdo->query("SELECT id FROM admins WHERE enabled=1 AND role='owner' ORDER BY id LIMIT 1")->fetchColumn();
        bulkCheck($owner!==false,'owner'); $token=bin2hex(random_bytes(32)); $session=hash('sha256',$token);
        $csrf=Celikom\Admin\AdminAuth::csrfForToken($token);
        $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES(?,?,?,UTC_TIMESTAMP()+INTERVAL 5 MINUTE)')->execute([$session,(int)$owner,hash('sha256',$csrf)]);
        $cookie=Celikom\Admin\AdminAuth::COOKIE.'='.$token;
        $page=bulkHttp('/admin?tab=uploads&status=pending&per_page=50',$cookie);
        bulkCheck($page[0]===200 && str_contains($page[1],'name="q"'),'https_page');
        if($hasPending) bulkCheck(str_contains($page[1],'data-bulk-all') && str_contains($page[1],'data-bulk-candidate'),'https_controls');
        else bulkCheck(!str_contains($page[1],'data-bulk-candidate') && str_contains($page[1],'Записей пока нет'),'https_empty_queue');
        $response=bulkHttp('/admin/bulk/preview',$cookie,['csrf'=>$csrf,'bulk_action'=>'approve','selected'=>$selected]);
        if($hasPending) bulkCheck($response[0]===200 && str_contains($response[1],'Одобрение: '.count($rows).' версий') && str_contains($response[1],'name="rights_confirmed"'),'https_preview');
        else bulkCheck($response[0]===409,'https_approved_preview_denied');
        foreach($inactiveSamples as $status=>$sample) {
            $page=bulkHttp('/admin?tab=uploads&status='.$status.'&per_page=50',$cookie);
            bulkCheck($page[0]===200 && str_contains($page[1],'name="selected['.$sample['id'].']"'),'https_inactive_checkbox_'.$status);
            $choice=[(int)$sample['id']=>$sample['version'].':'.$sample['active_id']];
            $preview=bulkHttp('/admin/bulk/preview',$cookie,['csrf'=>$csrf,'bulk_action'=>'delete','selected'=>$choice]);
            bulkCheck($preview[0]===200 && str_contains($preview[1],'name="confirm_count"') && str_contains($preview[1],'необходимая история сохранится'),'https_inactive_delete_preview_'.$status);
        }
        bulkCheck(bulkHttp('/admin/bulk/execute',$cookie,['csrf'=>'invalid','bulk_action'=>'approve','selected'=>$selected])[0]===403,'csrf_denied');
        bulkCheck(bulkHttp('/admin?tab=uploads')[0]===303,'anonymous_denied');
        bulkCheck(bulkHttp('/api/v1/config')[0]===200,'config');
    }
    $after=$pdo->query("SELECT COUNT(*) AS n,SUM(version) AS versions,SUM(is_active) AS active,SUM(status='pending') AS pending FROM track_replacements")->fetch(PDO::FETCH_ASSOC);
    bulkCheck($before===$after,'no_moderation_changes');
    echo 'ADMIN_REJECTED_CLEANUP_'.strtoupper($mode)."_PASS: controls, search, preview, version locks; no song approval or catalog changes\n";
} catch (Throwable $error) { $failure=$error instanceof PDOException ? 'db_state_'.$error->getCode() : $error->getMessage(); } finally { if($pdo && $session) $pdo->prepare('DELETE FROM admin_sessions WHERE token_hash=?')->execute([$session]); }

if(isset($failure)) { fwrite(STDERR,'ADMIN_REJECTED_SMOKE_FAILURE: '.$failure.PHP_EOL); exit(1); }
