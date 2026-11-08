<?php
declare(strict_types=1);

/**
 * CELIKOM read-only after-approval check of historical batch50.
 * Via SSH stdin; no saved production scripts, no DB modifications, no audio export.
 */
if (PHP_SAPI!=='cli' || count($argv)!==1) exit(2);
ini_set('display_errors','0');
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$ids=[
    '129803817' => 168,
    '113240879' => 169,
    '63607788' => 170,
    '133951915' => 171,
    '109996936' => 172,
    '136901411' => 173,
    '135266727' => 174,
    '137300019' => 175,
    '114382002' => 176,
    '60441408' => 177,
    '60441406' => 178,
    '93012496' => 179,
    '117219738' => 180,
    '146068411' => 181,
    '117711801' => 182,
    '131794594' => 183,
    '110945089' => 184,
    '120305627' => 185,
    '118112247' => 186,
    '138207906' => 187,
    '45439388' => 188,
    '148716092' => 189,
    '116649698' => 190,
    '108800777' => 191,
    '148716093' => 192,
    '125535652' => 193,
    '143062985' => 194,
    '70230156' => 195,
    '119890662' => 196,
    '106278184' => 197,
    '110263529' => 198,
    '131393815' => 199,
    '110263525' => 200,
    '119923185' => 201,
    '142577333' => 202,
    '137300022' => 203,
    '142577336' => 204,
    '142577359' => 205,
    '139910362' => 206,
    '137300018' => 207,
    '141077742' => 208,
    '141433322' => 209,
    '83405029' => 210,
    '115424578' => 211,
    '144874732' => 212,
    '83405024' => 213,
    '104242336' => 214,
    '134223771' => 215,
    '143934032' => 216,
    '73939469' => 217
];
try {
  $release=realpath($base.'/current');
  if (!is_link($base.'/current') || !$release || !str_starts_with($release,$base.'/releases/')
    || !is_file($release.'/bootstrap.php')) throw new RuntimeException('unsafe_active_release');
  require_once $release.'/bootstrap.php';
  $cfg=require $release.'/config/app.php';
  if (($cfg['environment']??'')!=='production') throw new RuntimeException('non_production');
  $pdo=\Celikom\Database\Connection::open($cfg);
  $storage=new \Celikom\Storage\LocalStorageAdapter($cfg['storage_path']);
  $catalog=new \Celikom\Repositories\PdoCatalogRepository($pdo);
  $app=new \Celikom\Application($cfg);
  $catalogue=(new \Celikom\Application\ReplacementCatalogueService($pdo))->snapshot();
  $inSnapshot=[];
  foreach($catalogue['tracks'] as $t){$inSnapshot[(string)$t['track_id']]=true;}
  $query=$pdo->prepare("SELECT t.id AS internal_track_id, t.service_track_id, r.id AS rid,
      r.status,r.is_active,r.version,r.approved_at,r.approved_by_admin_id,r.disabled_at,
      a.storage_driver,a.storage_key,a.sha256,a.size_bytes,a.mime_type,a.duration_ms
      FROM tracks t LEFT JOIN track_replacements r ON r.track_id=t.id
      LEFT JOIN audio_assets a ON a.id=r.audio_asset_id
      WHERE t.service='yandex' AND t.service_track_id=?
      ORDER BY r.id DESC");
  $summary=['status'=>'READ_ONLY','sample'=>count($ids),'approved_active'=>0,
     'pending'=>0,'rejected'=>0,'disabled'=>0,'missing'=>0,
     'snapshot_present'=>0,'asset_valid'=>0,'resolve_found'=>0,'head_200'=>0,
     'range_206'=>0,'duplicate_versions'=>0,'inconsistencies'=>[],'writes'=>0];
  $auth='Bearer '.(string)($cfg['test_api_token']??'');
  foreach($ids as $id=>$expectedRid) {
    $qrows=[];$query->execute([$id]);
    while($r=$query->fetch(PDO::FETCH_ASSOC))$qrows[]=$r;
    if(!$qrows){$summary['missing']++;$summary['inconsistencies'][]=['id'=>$id,'reason'=>'track_missing'];continue;}
    if(count($qrows)!==1){$summary['duplicate_versions']++;$summary['inconsistencies'][]=['id'=>$id,'reason'=>'multiple_versions'];}
    $row=$qrows[0];
    if((int)$row['rid']!==$expectedRid){$summary['inconsistencies'][]=['id'=>$id,'reason'=>'replacement_mismatch'];continue;}
    $state=(string)$row['status'];
    $active=(int)$row['is_active']===1;
    if($state==='approved' && $active && $row['disabled_at']===null){
       $summary['approved_active']++;
    } else {
       if(isset($summary[$state]))$summary[$state]++;
       else $summary['inconsistencies'][]=['id'=>$id,'reason'=>'status_'.$state.($active?'_active':'')];
       continue;
    }
    if($row['approved_at']===null || $row['approved_by_admin_id']===null || (int)$row['version']<2)
       $summary['inconsistencies'][]=['id'=>$id,'reason'=>'approval_metadata_incomplete'];
    if(isset($inSnapshot[$id]))$summary['snapshot_present']++;
    else $summary['inconsistencies'][]=['id'=>$id,'reason'=>'catalogue_missing'];
    $mapping=$catalog->findActive('yandex',$id);
    if(!$mapping || (int)$mapping['replacement_id']!==$expectedRid){
       $summary['inconsistencies'][]=['id'=>$id,'reason'=>'catalogue_mapping_missing'];continue;
    }
    $key=(string)$row['storage_key'];$size=(int)$row['size_bytes'];
    if($row['storage_driver']!=='local' || !$storage->exists($key) || $size<1024
      || $storage->getSize($key)!==$size || $storage->getMimeType($key)!=='audio/mpeg'
      || $row['mime_type']!=='audio/mpeg') {
       $summary['inconsistencies'][]=['id'=>$id,'reason'=>'audio_storage_invalid'];continue;
    }
    $summary['asset_valid']++;
    $r=$app->handle('GET','/api/v1/resolve',['service'=>'yandex','track_id'=>$id],['authorization'=>$auth],'');
    $data=json_decode($r->body,true);
    if($r->status!==200 || !is_array($data) || ($data['found']??false)!==true
      || (int)($data['replacement_id']??0)!==$expectedRid || !isset($data['audio_url'])) {
       $summary['inconsistencies'][]=['id'=>$id,'reason'=>'resolve_not_found_status_'. $r->status];continue;
    }
    $summary['resolve_found']++;
    $url=parse_url((string)$data['audio_url']);
    if(!is_array($url)||!preg_match('~^/api/v1/audio/[1-9][0-9]{0,17}$~D',(string)($url['path']??''))){
       $summary['inconsistencies'][]=['id'=>$id,'reason'=>'invalid_signed_audio_path'];continue;
    }
    parse_str((string)($url['query']??''),$params);
    $head=$app->handle('HEAD',$url['path'],$params,[],'');
    if($head->status===200 && ($head->headers['Content-Type']??'')==='audio/mpeg'
      && (int)($head->headers['Content-Length']??0)===$size
      && ($head->headers['Accept-Ranges']??'')==='bytes'){
       $summary['head_200']++;
    } else {
       $summary['inconsistencies'][]=['id'=>$id,'reason'=>'head_not_200'];continue;
    }
    $range=$app->handle('GET',$url['path'],$params,['range'=>'bytes=0-63'],'');
    if($range->status!==206 || (int)($range->headers['Content-Length']??0)!==64
       || ($range->headers['Content-Range']??'')!=='bytes 0-63/'.$size){
       $summary['inconsistencies'][]=['id'=>$id,'reason'=>'range_not_206'];continue;
    }
    ob_start();
    $range->emitBody();
    $got=ob_get_clean();
    $fh=$storage->openStream($key);
    try { $expected=fread($fh,64); }
    finally { fclose($fh); }
    if(!is_string($got)||strlen($got)!==64||$got!==$expected){
       $summary['inconsistencies'][]=['id'=>$id,'reason'=>'range_bytes_mismatch'];continue;
    }
    $summary['range_206']++;
  }
  $summary['catalogue_total_active']=$catalogue['total_tracks'];
  $summary['read_only_verified']=
      $summary['approved_active']===50 && $summary['snapshot_present']===50
      && $summary['asset_valid']===50 && $summary['resolve_found']===50
      && $summary['head_200']===50 && $summary['range_206']===50
      && $summary['duplicate_versions']===0 && count($summary['inconsistencies'])===0;
  echo json_encode($summary,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR),"\n";
  if(!$summary['read_only_verified'])exit(1);
} catch(Throwable $error) {
  fwrite(STDERR,"READ_ONLY_CHECK_ERROR: ".get_class($error).": ".$error->getMessage()."\n");exit(2);
}
