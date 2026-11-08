<?php
declare(strict_types=1);

/** Preflight read-only live DB filter. No audio files, no writes. */
if (PHP_SAPI !== 'cli' || count($argv) !== 1) exit(2);
ini_set('display_errors','0');
$base = '/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$stage = __DIR__;
try {
    if (is_link($stage) || !preg_match('~^'.preg_quote($base,'~').'/incoming/blur-fifty-[0-9]{8,16}$~D',$stage)
        || realpath($stage)!==$stage) throw new RuntimeException('unsafe_staging');
    $rel=realpath($base.'/current');
    if (!is_link($base.'/current') || !$rel || !str_starts_with($rel,$base.'/releases/'))
        throw new RuntimeException('unsafe_release');
    require $rel.'/bootstrap.php';
    $config=require $rel.'/config/app.php';
    if ($config['environment']!=='production') throw new RuntimeException('not_production');
    $items=json_decode(file_get_contents($stage.'/candidates.json'),true,512,JSON_THROW_ON_ERROR);
    if (($items['source_commit']??'')!=='10187b7af56f311fe141a3c9b75483798bf0f589'
        || ($items['target_pending']??null)!==50 || count($items['candidates']??[])<100)
        throw new RuntimeException('invalid_source_manifest');
    $pdo=\Celikom\Database\Connection::open($config);
    $pdo->exec('START TRANSACTION READ ONLY');
    $get=$pdo->prepare("SELECT id FROM tracks WHERE service='yandex' AND service_track_id=? LIMIT 1");
    $req=$pdo->prepare("SELECT id FROM track_requests WHERE service='yandex' AND service_track_id=? LIMIT 1");
    $tomb=$pdo->prepare("SELECT replacement_id FROM bulk_moderation_tombstones WHERE service='yandex' AND service_track_id=? LIMIT 1");
    $same=$pdo->prepare("SELECT service_track_id FROM tracks WHERE service='yandex' AND LOWER(TRIM(artist))=LOWER(TRIM(?)) AND LOWER(TRIM(title))=LOWER(TRIM(?)) LIMIT 1");
    $eligible=[];$skipped=[];$seen=[];
    foreach($items['candidates'] as $item) {
        $id=$item['id']??'';
        if(!is_string($id)||!preg_match('/^[1-9][0-9]{0,19}$/D',$id)||isset($seen[$id]))
            throw new RuntimeException('invalid_or_repeated_track_id');
        $seen[$id]=true;
        $get->execute([$id]);$a=$get->fetchColumn();
        $req->execute([$id]);$b=$req->fetchColumn();
        $tomb->execute([$id]);$d=$tomb->fetchColumn();
        $same->execute([$item['artist'],$item['title']]);$c=$same->fetchColumn();
        $why=$a!==false?'track_exists':($b!==false?'request_exists':($d!==false?'previously_deleted':($c!==false?'matching_title_other_track':'')));
        if($why==='') $eligible[]=$id;
        else $skipped[]=['id'=>$id,'reason'=>$why,'other_id'=>$why==='matching_title_other_track'?(string)$c:null];
    }
    $pdo->rollBack();
    echo json_encode(['status'=>'READ_ONLY','eligible'=>$eligible,'skipped'=>$skipped,'scanned'=>count($seen),'writes'=>0],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
} catch(Throwable $e) {
    if(isset($pdo)&&$pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,"PRECHECK_REFUSED: ".$e->getMessage()."\n");exit(1);
}
