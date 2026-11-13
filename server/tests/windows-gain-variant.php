<?php
declare(strict_types=1);
require dirname(__DIR__).'/bootstrap.php';

use Celikom\Application\AudioTokenService;
use Celikom\Application\ResolveService;
use Celikom\Application\WindowsGainVariant;
use Celikom\Http\AudioController;
use Celikom\Repositories\CatalogRepository;
use Celikom\Storage\LocalStorageAdapter;

function check(bool $passed, string $name): void {
    if (!$passed) throw new RuntimeException('W91_TEST_FAILED:'.$name);
}
function body(\Celikom\Http\Response $response): string {
    ob_start();
    $response->emitBody();
    return (string)ob_get_clean();
}
$root=sys_get_temp_dir().'/celikom-w91-'.bin2hex(random_bytes(6));
$store=new LocalStorageAdapter($root);
$original=str_repeat('SYNTHETIC_ORIGINAL_MP3_BYTES', 160);
$derived=str_repeat('SYNTHETIC_GAIN_RENDER_BYTES', 170);
$sourceSha=hash('sha256',$original);
$variantSha=hash('sha256',$derived);
$sourceKey='audio/'.substr($sourceSha,0,2).'/'.$sourceSha.'.mp3';
$variantKey='windows-gain/'.substr($variantSha,0,2).'/'.$variantSha.'.mp3';
foreach ([$sourceKey=>$original,$variantKey=>$derived] as $key=>$bytes) {
    $file=fopen('php://temp','w+b');fwrite($file,$bytes);rewind($file);
    $store->put($key,$file);fclose($file);
}
$catalog=new class($sourceSha,$sourceKey,$original,$variantSha,$variantKey,$derived) implements CatalogRepository {
    public array $row;
    public function __construct(string $sha, string $key, string $source, string $vsha,
                                string $vkey, string $variant) {
        $this->row=[
            'replacement_id'=>71,'version'=>3,'gain_db'=>11.5,'storage_driver'=>'local',
            'storage_key'=>$key,'sha256'=>$sha,'mime_type'=>'audio/mpeg',
            'size_bytes'=>strlen($source),'duration_ms'=>190000,
            'windows_variant_source_sha256'=>$sha,'windows_variant_source_version'=>3,
            'windows_variant_gain_db'=>11.5,'windows_variant_storage_key'=>$vkey,
            'windows_variant_sha256'=>$vsha,'windows_variant_mime_type'=>'audio/mpeg',
            'windows_variant_size_bytes'=>strlen($variant),'windows_variant_duration_ms'=>190000
        ];
    }
    public function findActive(string $service,string $trackId):?array {
        return $service==='yandex' && $trackId==='40371622' ? $this->row : null;
    }
    public function findByReplacement(int $id):?array {
        return $id===71?$this->row:null;
    }
};
$tokens=new AudioTokenService(str_repeat('W91_TEST_SIGNING_KEY_',4));
$resolver=new ResolveService($catalog,$store,$tokens);
$access=['session_id'=>26,'valid_until'=>null,'refresh_expires_at'=>gmdate('Y-m-d H:i:s',time()+3600)];
try {
    $browser=$resolver->resolve('yandex','40371622',$access,false,false);
    check($browser['found']===true && $browser['gain_db']===11.5
        && $browser['gain_applied']===false && !str_contains($browser['audio_url'],'variant='),
        'browser unchanged raw source');
    $win=$resolver->resolve('yandex','40371622',$access,false,true);
    check($win['found']===true && $win['gain_applied']===true
        && str_contains($win['audio_url'],'variant=windows_gain_v1'), 'Windows variant explicitly selected');
    parse_str((string)parse_url($win['audio_url'],PHP_URL_QUERY),$params);
    parse_str((string)parse_url($browser['audio_url'],PHP_URL_QUERY),$normalParams);
    check($tokens->validWindowsGain(71,3,$params['expires'],$params['token'],
        26,$variantSha), 'variant bound to exact source/version/session/hash');
    check(!$tokens->valid(71,3,$params['expires'],$params['token'],sessionId:26),
        'variant HMAC cannot authorize raw audio');
    check(!$tokens->validWindowsGain(71,3,$params['expires'],$normalParams['token'],
        26,$variantSha),'raw HMAC cannot authorize variant');
    check(!$tokens->validWindowsGain(71,3,$params['expires'],$params['token'],
        27,$variantSha),'other user session denied');
    check(!$tokens->validWindowsGain(71,3,$params['expires'],$params['token'],
        26,str_repeat('0',64)),'other rendered digest denied');

    // Access service intentionally omitted only in synthetic isolated unit
    // test. Production AudioController still enforces each real Range session.
    $http=new AudioController($catalog,$store,$tokens);
    $range=$http->handle('GET',71,$params,['range'=>'bytes=7-30']);
    check($range->status===206 && body($range)===substr($derived,7,24)
        && $range->headers['ETag']==='"'.$variantSha.'-3"', 'signed variant Range206 exact bytes and ETag');
    check($http->handle('HEAD',71,$params,[])->headers['Content-Length']===strval(strlen($derived)),
        'variant HEAD size');
    check($http->handle('GET',71,$params,['range'=>'bytes=7-30','if-range'=>'"wrong"'])->status===200,
        'If-Range mismatch uses entire approved representation');
    check($http->handle('GET',71,$normalParams,[])->status===200 &&
        body($http->handle('GET',71,$normalParams,[]))===$original,'browser original unchanged');
    $tampered=$params;unset($tampered['variant']);
    check($http->handle('GET',71,$tampered,[])->status===403,'variant token not valid on original route');
    $tampered=$normalParams;$tampered['variant']='windows_gain_v1';
    check($http->handle('GET',71,$tampered,[])->status===403,'original token not valid on Windows route');

    foreach ([
        ['gain'=>9.5],['version'=>4],['sha'=>str_repeat('a',64)],
        ['size'=>strlen($derived)+1],['duration'=>192000],['missing'=>true]
    ] as $mutate) {
        $before=$catalog->row;
        if (isset($mutate['gain'])) $catalog->row['gain_db']=$mutate['gain'];
        if (isset($mutate['version'])) $catalog->row['version']=$mutate['version'];
        if (isset($mutate['sha'])) $catalog->row['sha256']=$mutate['sha'];
        if (isset($mutate['size'])) $catalog->row['windows_variant_size_bytes']=$mutate['size'];
        if (isset($mutate['duration'])) $catalog->row['windows_variant_duration_ms']=$mutate['duration'];
        if (isset($mutate['missing'])) $catalog->row['windows_variant_storage_key']='windows-gain/aa/'.str_repeat('a',64).'.mp3';
        check(WindowsGainVariant::select($catalog->row,$store)===null,'stale sidecar strictly excluded');
        $fallback=$resolver->resolve('yandex','40371622',$access,false,true);
        check($fallback['gain_applied']===false && !str_contains($fallback['audio_url'],'variant='),
            'unready Windows gain never mislabeled applied');
        check($http->handle('GET',71,$params,[])->status===403,
            'stale signed variant denied without falling back to original');
        $catalog->row=$before;
    }
    $anonymous=$resolver->resolve('yandex','40371622',null,false,true);
    check($anonymous['gain_applied']===false,'no session no Windows gain stream');
    echo "W91_SIGNED_WINDOWS_GAIN_VARIANT_AND_BROWSER_ORIGINAL_PASS\n";
} finally {
    foreach ([$sourceKey,$variantKey] as $key) $store->delete($key);
}
