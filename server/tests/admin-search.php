<?php
declare(strict_types=1);
require dirname(__DIR__).'/bootstrap.php';
use Celikom\Admin\AdminPanel;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Storage\LocalStorageAdapter;
function searchCheck(bool $ok,string $message): void { if (!$ok) throw new RuntimeException($message); }
$config=require dirname(__DIR__).'/config/app.php';
searchCheck(str_starts_with($config['db_name'],'celikom_test'),'Disposable database required');
$pdo=Connection::open($config);
(new MigrationRunner($pdo,dirname(__DIR__).'/migrations'))->run();
$panel=new AdminPanel($pdo,new LocalStorageAdapter(sys_get_temp_dir().'/celikom-search-tests'));
$uploads=new ReflectionMethod(AdminPanel::class,'uploads');
$requests=new ReflectionMethod(AdminPanel::class,'requests');
$normalize=new ReflectionMethod(AdminPanel::class,'songSearch');
$nonce='search'.bin2hex(random_bytes(5));
$pdo->beginTransaction();
try {
    $pdo->prepare('INSERT INTO audio_assets(storage_driver,storage_key,sha256,mime_type,size_bytes,duration_ms) VALUES(?,?,?,?,?,?)')
        ->execute(['local','audio/'.$nonce.'.mp3',hash('sha256',$nonce),'audio/mpeg',1234,150000]);
    $asset=(int)$pdo->lastInsertId();
    $ids=[];
    for($i=0;$i<14;$i++) {
        $id=(string)(800000000000+random_int(1,999999999));$ids[]=$id;
        $artist='ИсполнительТест '.$nonce;
        $title=($i===0?'РанняяПесня':($i===12?'Литерал!%_':($i===13?'ЛитералZZ':'ПесняТест'))).' '.$nonce;
        $pdo->prepare('INSERT INTO tracks(service,service_track_id,artist,title,duration_ms) VALUES(?,?,?,?,?)')
            ->execute(['yandex',$id,$artist,$title,$i===13?140000:150000]);
        $track=(int)$pdo->lastInsertId();
        $pdo->prepare('INSERT INTO track_replacements(track_id,audio_asset_id,status,is_active) VALUES(?,?,?,0)')
            ->execute([$track,$asset,$i===13?'rejected':'pending']);
        $pdo->prepare('INSERT INTO track_requests(service,service_track_id,artist,title,uploader_hash,status) VALUES(?,?,?,?,?,?)')
            ->execute(['yandex',$id,$artist,$title,hash('sha256',$nonce.$i),'pending']);
    }
    $render=static fn(array $q):string=>$uploads->invoke($panel,['role'=>'viewer'],'qa-csrf',$q);
    $assertCount=static function(string $html,int $count):void{searchCheck(str_contains($html,'Всего: '.$count.' ·'),'Filtered count '.$count);};
    $first=$render(['q'=>$nonce,'per_page'=>'10']);$assertCount($first,14);
    searchCheck(!str_contains($first,'Track ID '.$ids[0].'</div>'),'Oldest fixture beyond first page');
    searchCheck(str_contains($first,'q='.$nonce.'&amp;page=2'),'Pagination keeps search');
    $second=$render(['q'=>$nonce,'per_page'=>'10','page'=>'2']);$assertCount($second,14);
    searchCheck(str_contains($second,$ids[0]),'Second page works');
    foreach([$ids[0],'ранняяпесня '.$nonce,$nonce.' исполнительтест ранняяпесня'] as $q) {
        $result=$render(['q'=>$q]);$assertCount($result,1);
        searchCheck(str_contains($result,$ids[0]),'Search across whole catalog, mixed case and reversed words');
    }
    $assertCount($render(['q'=>$nonce,'status'=>'rejected']),1);
    $assertCount($render(['q'=>$nonce,'duration'=>'compatible']),13);
    $assertCount($render(['q'=>'Литерал!%_ '.$nonce]),1);
    $none=$render(['q'=>"' OR 1=1 -- ".$nonce]);$assertCount($none,0);
    searchCheck(str_contains($none,'Песни не найдены'),'Useful empty result');
    $hostile=$render(['q'=>'"><script>alert(1)</script>']);
    searchCheck(!str_contains($hostile,'<script>alert(1)</script>')&&str_contains($hostile,'&lt;script&gt;'),'HTML escaped');
    searchCheck($normalize->invoke(null,['q'=>['bad']])===''&&$normalize->invoke(null,['q'=>"\xff"])==='','Invalid search ignored');
    searchCheck($normalize->invoke(null,['q'=>"  Тест\n  песня "])==='Тест песня','Whitespace normalized');
    searchCheck(preg_match('/^.{160}$/us',$normalize->invoke(null,['q'=>str_repeat('ы',200)]))===1,'UTF-8 character bound');
    foreach([$ids[0],'ранняяпесня '.$nonce] as $q) {
        $html=$requests->invoke($panel,['role'=>'viewer'],'qa-csrf',['q'=>$q,'status'=>'']);
        $assertCount($html,1);searchCheck(str_contains($html,$ids[0]),'Proposal queue search');
    }
    $proposalPages=$requests->invoke($panel,['role'=>'viewer'],'qa-csrf',['q'=>$nonce,'status'=>'','per_page'=>'10']);
    $assertCount($proposalPages,14);searchCheck(str_contains($proposalPages,'q='.$nonce.'&amp;page=2'),'Proposal pagination');
    echo "PASS admin search: title, artist, ID, case, multiple words, whole catalog, pagination, filters, literals, XSS/SQL input, proposals\n";
} finally { if($pdo->inTransaction())$pdo->rollBack(); }
