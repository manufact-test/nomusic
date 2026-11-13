<?php
declare(strict_types=1);
ini_set('display_errors','0');
function searchAssert(bool $ok,string $code):void {if(!$ok)throw new RuntimeException($code);}
function searchHttp(string $path,string $cookie=''):array {
    searchAssert(str_starts_with($path,'/admin?tab=')||$path==='/api/v1/config','http_path');
    $ch=curl_init('https://darkred-camel-588676.hostingersite.com'.$path);
    curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_FOLLOWLOCATION=>false,
        CURLOPT_HTTPHEADER=>['Cache-Control: no-store','Cookie: '.$cookie],
        CURLOPT_SSL_VERIFYPEER=>true,CURLOPT_SSL_VERIFYHOST=>2,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>25]);
    $body=curl_exec($ch);$code=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);curl_close($ch);
    searchAssert(is_string($body)&&strlen($body)<2097152,'http_body');
    return [$code,$body];
}
$pdo=null;$sessionHash=null;
try {
    searchAssert(PHP_SAPI==='cli'&&$argc===3,'arguments');
    $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    $release=$root.'/releases/'.$argv[1];
    searchAssert(preg_match('/^admin-song-search-[a-f0-9]{12}$/D',$argv[1])===1&&in_array($argv[2],['candidate','active'],true),'release');
    if($argv[2]==='active')searchAssert(realpath($root.'/current')===$release,'active_release');
    require $release.'/bootstrap.php';$config=require $release.'/config/app.php';
    searchAssert($config['db_name']==='u235811320_celikom'&&$config['admin_enabled'],'site_config');
    $pdo=Celikom\Database\Connection::open($config);
    $before=$pdo->query('SELECT (SELECT COUNT(*) FROM tracks) AS tracks,(SELECT COUNT(*) FROM track_replacements) AS versions,(SELECT COUNT(*) FROM audio_assets) AS assets')->fetch();
    $sample=$pdo->query('SELECT t.service_track_id,t.title FROM tracks t JOIN track_replacements r ON r.track_id=t.id JOIN audio_assets a ON a.id=r.audio_asset_id ORDER BY r.id DESC LIMIT 1')->fetch();
    searchAssert(is_array($sample),'catalog_sample');
    $panel=new Celikom\Admin\AdminPanel($pdo,new Celikom\Storage\LocalStorageAdapter($config['storage_path']));
    $uploads=new ReflectionMethod(Celikom\Admin\AdminPanel::class,'uploads');
    $requests=new ReflectionMethod(Celikom\Admin\AdminPanel::class,'requests');
    $id=(string)$sample['service_track_id'];$marker='celikomsearchqa'.bin2hex(random_bytes(8));
    $html=$uploads->invoke($panel,['role'=>'owner'],'qa-unused',['q'=>$id]);
    searchAssert(str_contains($html,'name="q"')&&str_contains($html,'Track ID '.$id.'</div>'),'candidate_track_search');
    $none=$uploads->invoke($panel,['role'=>'owner'],'qa-unused',['q'=>$marker]);
    searchAssert(str_contains($none,'Всего: 0 ·')&&str_contains($none,'Песни не найдены'),'candidate_empty_search');
    $proposal=$requests->invoke($panel,['role'=>'owner'],'qa-unused',['q'=>$marker,'status'=>'']);
    searchAssert(str_contains($proposal,'Всего: 0 ·')&&str_contains($proposal,'name="q"'),'candidate_proposal_search');
    if($argv[2]==='active') {
        $owner=$pdo->query("SELECT id FROM admins WHERE role='owner' AND enabled=1 ORDER BY id LIMIT 1")->fetchColumn();
        searchAssert($owner!==false,'existing_owner');
        $token=bin2hex(random_bytes(32));$sessionHash=hash('sha256',$token);
        $pdo->prepare('INSERT INTO admin_sessions(token_hash,admin_id,csrf_hash,expires_at) VALUES(?,?,?,UTC_TIMESTAMP()+INTERVAL 5 MINUTE)')
            ->execute([$sessionHash,(int)$owner,hash('sha256',Celikom\Admin\AdminAuth::csrfForToken($token))]);
        $cookie=Celikom\Admin\AdminAuth::COOKIE.'='.$token;
        $ready=false;
        for($i=0;$i<8;$i++) {
            $page=searchHttp('/admin?tab=uploads&q='.rawurlencode($id),$cookie);
            if($page[0]===200&&str_contains($page[1],'name="q"')&&str_contains($page[1],'Track ID '.$id.'</div>')){$ready=true;break;}
            usleep(1000000);
        }
        searchAssert($ready,'https_search_ready');
        foreach(['uploads','requests'] as $tab) {
            $page=searchHttp('/admin?tab='.$tab.'&status=&q='.$marker,$cookie);
            searchAssert($page[0]===200&&str_contains($page[1],'Всего: 0 ·')&&str_contains($page[1],'name="q"'),'https_empty_'.$tab);
        }
        searchAssert(searchHttp('/admin?tab=uploads&q='.$id)[0]===303,'anonymous_admin_denied');
        searchAssert(searchHttp('/api/v1/config')[0]===200,'public_config_healthy');
    }
    $after=$pdo->query('SELECT (SELECT COUNT(*) FROM tracks) AS tracks,(SELECT COUNT(*) FROM track_replacements) AS versions,(SELECT COUNT(*) FROM audio_assets) AS assets')->fetch();
    searchAssert($before===$after,'catalog_counts_unchanged');
    echo 'ADMIN_SEARCH_'.strtoupper($argv[2])."_PASS: real catalog search, missing result, proposal search; no catalog writes\n";
} finally {
    if($pdo&&$sessionHash)$pdo->prepare('DELETE FROM admin_sessions WHERE token_hash=?')->execute([$sessionHash]);
}
