<?php

declare(strict_types=1);
require __DIR__ . '/smoke.php';
use Celikom\Application\M4aInspector;
use Celikom\Application\UploadService;
use Celikom\Application\ResolveService;
use Celikom\Application\AudioTokenService;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Repositories\PdoCatalogRepository;
use Celikom\Storage\LocalStorageAdapter;
$config = require dirname(__DIR__) . '/config/app.php';
if (!str_starts_with((string)$config['db_name'], 'celikom_test')) throw new RuntimeException('Disposable database required');
$pdo=Connection::open($config);(new MigrationRunner($pdo,dirname(__DIR__).'/migrations'))->run();
$storage=new LocalStorageAdapter($config['storage_path']);$path=$argv[1];$ms=(new M4aInspector())->durationMs($path);
expect($ms !== null,'Real AAC fixture');
$upload=new UploadService($pdo,$storage,31457280,static fn($p)=>is_file($p));
$fields=['service'=>'yandex','track_id'=>'799461','duration_ms'=>(string)$ms,'artist'=>'Synthetic','title'=>'M4A regression','album'=>'','declaration'=>'1','request_id'=>'10000000-0000-4000-8000-000000046001'];
$file=['error'=>UPLOAD_ERR_OK,'tmp_name'=>$path,'name'=>'fixture.M4A','size'=>filesize($path)];
$result=$upload->upload($fields,$file,hash('sha256','m4a-isolated-test'));$id=$result['replacement_id'];
expect($result['status']==='pending','M4A requires moderation');
$q=$pdo->prepare('SELECT a.* FROM audio_assets a JOIN track_replacements r ON r.audio_asset_id=a.id WHERE r.id=?');$q->execute([$id]);$asset=$q->fetch(PDO::FETCH_ASSOC);
expect($asset['mime_type']==='audio/mp4' && str_ends_with($asset['storage_key'],'.m4a'),'Original M4A stored');
expect(hash_equals($asset['sha256'],hash_file('sha256',$path)),'No transcoding');
$catalog=new PdoCatalogRepository($pdo);$resolver=new ResolveService($catalog,$storage,new AudioTokenService(str_repeat('m4a-test-key-',4),600));
expect(!$resolver->resolve('yandex','799461',null,true)['found'],'Pending M4A hidden');
$again=$upload->upload($fields,$file,hash('sha256','m4a-isolated-test'));expect($again['duplicate'],'M4A retry idempotent');
$bad=$fields;$bad['track_id']='799462';$bad['duration_ms']=(string)($ms+1501);$bad['request_id']='10000000-0000-4000-8000-000000046002';
try{$upload->upload($bad,$file,hash('sha256','m4a-isolated-test'));throw new RuntimeException('Duration mismatch accepted');}catch(DomainException $e){expect($e->getMessage()==='duration_mismatch','Duration mismatch blocked');}
// Disposable CI-only approval to verify signed delivery compatibility.
$pdo->prepare("UPDATE track_replacements SET status='approved',is_active=1 WHERE id=?")->execute([$id]);
expect(!$resolver->resolve('yandex','799461')['found'],'Old clients retain original rather than unsupported M4A');
$resolved=$resolver->resolve('yandex','799461',null,true);expect($resolved['found']&&$resolved['mime_type']==='audio/mp4','New client resolves M4A');
$auth=['Authorization'=>'Bearer '.str_repeat('m4a-test-',8)];$config['test_api_token']=str_repeat('m4a-test-',8);$config['api_enabled']=true;$config['audio_signing_key']=str_repeat('m4a-test-key-',4);
parse_str(parse_url($resolved['audio_url'],PHP_URL_QUERY),$query);
$app=new Celikom\Application($config);$response=$app->handle('GET','/api/v1/audio/'.$id,$query,['Range'=>'bytes=0-1023']);
expect($response->status===206 && $response->headers['Content-Type']==='audio/mp4' && bytes($response)===substr(file_get_contents($path),0,1024),'Signed M4A Range serves exact source bytes');
// All fixtures stay in the disposable CI database, like the existing upload suite.
fwrite(STDOUT,"PASS M4A upload, moderation, duplicate, duration gate, backward compatibility and signed Range\n");
