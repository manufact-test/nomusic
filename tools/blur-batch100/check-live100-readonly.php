<?php
declare(strict_types=1);
// Owner requested non-mutating live verification of two real CELIKOM 50-song batches.
// Run via protected GitHub Actions SSH stdin. Never echoes credentials, audio URLs or user info.
if(PHP_SAPI!=='cli' || count($argv)!==1)exit(2);
ini_set('display_errors','0');
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$expected=[
  '57020069' => ['rid'=>218, 'size'=>7315772, 'batch'=>1],
  '133378523' => ['rid'=>219, 'size'=>6427796, 'batch'=>1],
  '66501221' => ['rid'=>220, 'size'=>7961518, 'batch'=>1],
  '110263534' => ['rid'=>221, 'size'=>3565654, 'batch'=>1],
  '36142272' => ['rid'=>222, 'size'=>7150281, 'batch'=>1],
  '84382255' => ['rid'=>223, 'size'=>5209278, 'batch'=>1],
  '75425467' => ['rid'=>224, 'size'=>6363891, 'batch'=>1],
  '109990536' => ['rid'=>225, 'size'=>4377245, 'batch'=>1],
  '110263527' => ['rid'=>226, 'size'=>4171417, 'batch'=>1],
  '110263532' => ['rid'=>227, 'size'=>4014960, 'batch'=>1],
  '108809115' => ['rid'=>228, 'size'=>5166437, 'batch'=>1],
  '106155608' => ['rid'=>229, 'size'=>5109674, 'batch'=>1],
  '110263522' => ['rid'=>230, 'size'=>2830046, 'batch'=>1],
  '110263523' => ['rid'=>231, 'size'=>4638764, 'batch'=>1],
  '109990539' => ['rid'=>232, 'size'=>5252863, 'batch'=>1],
  '109990535' => ['rid'=>233, 'size'=>5247645, 'batch'=>1],
  '109990537' => ['rid'=>234, 'size'=>4429500, 'batch'=>1],
  '109990532' => ['rid'=>235, 'size'=>6450346, 'batch'=>1],
  '109990527' => ['rid'=>236, 'size'=>4661455, 'batch'=>1],
  '109990538' => ['rid'=>237, 'size'=>6782618, 'batch'=>1],
  '109990526' => ['rid'=>238, 'size'=>5589391, 'batch'=>1],
  '109990531' => ['rid'=>239, 'size'=>6174513, 'batch'=>1],
  '103844888' => ['rid'=>240, 'size'=>4478621, 'batch'=>1],
  '103844886' => ['rid'=>241, 'size'=>5336462, 'batch'=>1],
  '103844890' => ['rid'=>242, 'size'=>4594583, 'batch'=>1],
  '104427920' => ['rid'=>243, 'size'=>4402334, 'batch'=>1],
  '103844891' => ['rid'=>244, 'size'=>5752355, 'batch'=>1],
  '103844892' => ['rid'=>245, 'size'=>4802521, 'batch'=>1],
  '67349423' => ['rid'=>246, 'size'=>5047110, 'batch'=>1],
  '81549433' => ['rid'=>247, 'size'=>7328330, 'batch'=>1],
  '129653784' => ['rid'=>248, 'size'=>3859270, 'batch'=>1],
  '139979379' => ['rid'=>249, 'size'=>4951815, 'batch'=>1],
  '133429871' => ['rid'=>250, 'size'=>8049708, 'batch'=>1],
  '109070388' => ['rid'=>251, 'size'=>5091184, 'batch'=>1],
  '111248482' => ['rid'=>252, 'size'=>3865121, 'batch'=>1],
  '136598165' => ['rid'=>253, 'size'=>5180648, 'batch'=>1],
  '110132825' => ['rid'=>254, 'size'=>3935129, 'batch'=>1],
  '62567305' => ['rid'=>255, 'size'=>7886285, 'batch'=>1],
  '65875047' => ['rid'=>256, 'size'=>7550617, 'batch'=>1],
  '105833872' => ['rid'=>257, 'size'=>3998868, 'batch'=>1],
  '122988102' => ['rid'=>258, 'size'=>4184860, 'batch'=>1],
  '113964655' => ['rid'=>259, 'size'=>3866949, 'batch'=>1],
  '105006649' => ['rid'=>260, 'size'=>4493105, 'batch'=>1],
  '144098514' => ['rid'=>261, 'size'=>4666557, 'batch'=>1],
  '36327441' => ['rid'=>262, 'size'=>8513872, 'batch'=>1],
  '143233927' => ['rid'=>263, 'size'=>3856761, 'batch'=>1],
  '106941620' => ['rid'=>264, 'size'=>6128115, 'batch'=>1],
  '125996700' => ['rid'=>265, 'size'=>4805530, 'batch'=>1],
  '70743630' => ['rid'=>266, 'size'=>6834074, 'batch'=>1],
  '118456194' => ['rid'=>267, 'size'=>7277743, 'batch'=>1],
  '35758334' => ['rid'=>268, 'size'=>8591195, 'batch'=>2],
  '131737642' => ['rid'=>269, 'size'=>3568371, 'batch'=>2],
  '136101923' => ['rid'=>270, 'size'=>4403014, 'batch'=>2],
  '136101915' => ['rid'=>271, 'size'=>4144924, 'batch'=>2],
  '136101919' => ['rid'=>272, 'size'=>4631847, 'batch'=>2],
  '130793649' => ['rid'=>273, 'size'=>3789889, 'batch'=>2],
  '143286547' => ['rid'=>274, 'size'=>4379167, 'batch'=>2],
  '119057925' => ['rid'=>275, 'size'=>3977720, 'batch'=>2],
  '123214891' => ['rid'=>276, 'size'=>6012387, 'batch'=>2],
  '132395442' => ['rid'=>277, 'size'=>4531494, 'batch'=>2],
  '148716987' => ['rid'=>278, 'size'=>4591744, 'batch'=>2],
  '124666563' => ['rid'=>279, 'size'=>7448032, 'batch'=>2],
  '146451124' => ['rid'=>280, 'size'=>4774183, 'batch'=>2],
  '72063039' => ['rid'=>281, 'size'=>3931368, 'batch'=>2],
  '148716967' => ['rid'=>282, 'size'=>4879870, 'batch'=>2],
  '38572746' => ['rid'=>283, 'size'=>5328376, 'batch'=>2],
  '61212406' => ['rid'=>284, 'size'=>6754682, 'batch'=>2],
  '42486164' => ['rid'=>285, 'size'=>7346095, 'batch'=>2],
  '148421462' => ['rid'=>286, 'size'=>5463460, 'batch'=>2],
  '124666565' => ['rid'=>287, 'size'=>3911053, 'batch'=>2],
  '106475673' => ['rid'=>288, 'size'=>5148256, 'batch'=>2],
  '63934931' => ['rid'=>289, 'size'=>9288559, 'batch'=>2],
  '112412053' => ['rid'=>290, 'size'=>5428853, 'batch'=>2],
  '76711329' => ['rid'=>291, 'size'=>6928135, 'batch'=>2],
  '38439048' => ['rid'=>292, 'size'=>6952795, 'batch'=>2],
  '107857822' => ['rid'=>293, 'size'=>7821522, 'batch'=>2],
  '59367471' => ['rid'=>294, 'size'=>9149567, 'batch'=>2],
  '117929982' => ['rid'=>295, 'size'=>6316034, 'batch'=>2],
  '74013830' => ['rid'=>296, 'size'=>7175358, 'batch'=>2],
  '146521531' => ['rid'=>297, 'size'=>3087717, 'batch'=>2],
  '119296534' => ['rid'=>298, 'size'=>5175842, 'batch'=>2],
  '136315543' => ['rid'=>299, 'size'=>3707718, 'batch'=>2],
  '27898785' => ['rid'=>300, 'size'=>10110873, 'batch'=>2],
  '112047071' => ['rid'=>301, 'size'=>4190941, 'batch'=>2],
  '121793166' => ['rid'=>302, 'size'=>7143384, 'batch'=>2],
  '127293321' => ['rid'=>303, 'size'=>6926359, 'batch'=>2],
  '74017773' => ['rid'=>304, 'size'=>11901432, 'batch'=>2],
  '80408120' => ['rid'=>305, 'size'=>8596837, 'batch'=>2],
  '48591491' => ['rid'=>306, 'size'=>12692849, 'batch'=>2],
  '36161925' => ['rid'=>307, 'size'=>5763074, 'batch'=>2],
  '126980903' => ['rid'=>308, 'size'=>4197355, 'batch'=>2],
  '94832019' => ['rid'=>309, 'size'=>7156968, 'batch'=>2],
  '107970520' => ['rid'=>310, 'size'=>11100392, 'batch'=>2],
  '80305534' => ['rid'=>311, 'size'=>6864397, 'batch'=>2],
  '138472605' => ['rid'=>312, 'size'=>8171042, 'batch'=>2],
  '43854379' => ['rid'=>313, 'size'=>6477784, 'batch'=>2],
  '43854376' => ['rid'=>314, 'size'=>6477784, 'batch'=>2],
  '43504909' => ['rid'=>315, 'size'=>10186127, 'batch'=>2],
  '106475672' => ['rid'=>316, 'size'=>5691540, 'batch'=>2],
  '63607794' => ['rid'=>317, 'size'=>8444877, 'batch'=>2]
];
try{
 $rel=realpath($base.'/current');
 if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/')||!is_file($rel.'/bootstrap.php'))throw new RuntimeException('unsafe_release');
 require_once $rel.'/bootstrap.php';
 $cfg=require $rel.'/config/app.php';
 if(($cfg['environment']??'')!=='production')throw new RuntimeException('wrong_environment');
 $pdo=\Celikom\Database\Connection::open($cfg);
 $store=new \Celikom\Storage\LocalStorageAdapter($cfg['storage_path']);
 $repo=new \Celikom\Repositories\PdoCatalogRepository($pdo);
 $app=new \Celikom\Application($cfg);
 $catalogue=(new \Celikom\Application\ReplacementCatalogueService($pdo))->snapshot();
 $inCatalogue=[];
 foreach($catalogue['tracks'] as $item)$inCatalogue[(string)$item['track_id']]=true;
 $stmt=$pdo->prepare("SELECT t.service_track_id, r.id AS replacement_id,r.status,r.is_active,r.version,r.approved_at,r.approved_by_admin_id,r.disabled_at,
    a.storage_driver,a.storage_key,a.sha256,a.size_bytes,a.mime_type,a.duration_ms
    FROM tracks t JOIN track_replacements r ON r.track_id=t.id
    JOIN audio_assets a ON a.id=r.audio_asset_id
    WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.id");
 $summary=['status'=>'LIVE_READ_ONLY','checked'=>count($expected),'batch1'=>['total'=>0,'approved_active'=>0,'pending'=>0,'rejected'=>0,'disabled'=>0],
          'batch2'=>['total'=>0,'approved_active'=>0,'pending'=>0,'rejected'=>0,'disabled'=>0],
          'approved_active'=>0,'pending'=>0,'rejected'=>0,'disabled'=>0,'missing'=>0,'duplicate_versions'=>0,
          'asset_verified'=>0,'catalogue_present_active'=>0,'catalogue_correctly_absent_inactive'=>0,
          'resolve_found'=>0,'resolve_not_found_inactive'=>0,'head200'=>0,'range206'=>0,
          'other_statuses'=>[],'issues'=>[],'writes'=>0,'catalogue_total_active'=>(int)$catalogue['total_tracks']];
 $token=(string)($cfg['test_api_token']??'');
 if(strlen($token)<24)throw new RuntimeException('api_test_token_unavailable');
 foreach($expected as $trackId=>$e){
  $trackId=(string)$trackId;
  $batch='batch'.$e['batch'];
  $stmt->execute([$trackId]);$rows=$stmt->fetchAll(PDO::FETCH_ASSOC);
  if(!$rows){$summary['missing']++;$summary['issues'][]=['track'=>$trackId,'error'=>'not_present'];continue;}
  if(count($rows)!==1){$summary['duplicate_versions']++;$summary['issues'][]=['track'=>$trackId,'error'=>'multiple_versions'];continue;}
  $r=$rows[0];
  if((int)$r['replacement_id']!==$e['rid']){$summary['issues'][]=['track'=>$trackId,'error'=>'unexpected_replacement_id'];continue;}
  $summary[$batch]['total']++;
  $status=(string)$r['status'];
  $approved=$status==='approved'&&(int)$r['is_active']===1&&$r['disabled_at']===null;
  if($approved){
   $summary[$batch]['approved_active']++;$summary['approved_active']++;
   if($r['approved_at']===null || $r['approved_by_admin_id']===null || (int)$r['version']<2)
     $summary['issues'][]=['track'=>$trackId,'error'=>'approval_metadata_missing'];
  }elseif($status==='pending'&&(int)$r['is_active']===0){
   $summary[$batch]['pending']++;$summary['pending']++;
  }elseif(($status==='rejected'||$status==='disabled')&&(int)$r['is_active']===0){
   $summary[$batch][$status]++;$summary[$status]++;
  }else{
   $summary['issues'][]=['track'=>$trackId,'error'=>'unexpected_status_or_active'];
   $summary['other_statuses'][]=['track'=>$trackId,'status'=>$status,'active'=>(int)$r['is_active']];
   continue;
  }
  if((string)$r['storage_driver']!=='local' || !$store->exists((string)$r['storage_key']) ||
     $store->getSize((string)$r['storage_key'])!==(int)$r['size_bytes'] ||
     (int)$r['size_bytes']!==$e['size'] || $store->getMimeType((string)$r['storage_key'])!=='audio/mpeg' ||
     (string)$r['mime_type']!=='audio/mpeg' || (int)$r['duration_ms']<1000){
    $summary['issues'][]=['track'=>$trackId,'error'=>'audio_storage_mismatch'];continue;
  }
  $summary['asset_verified']++;
  $mapping=$repo->findActive('yandex',$trackId);
  $listed=isset($inCatalogue[$trackId]);
  $resp=$app->handle('GET','/api/v1/resolve',['service'=>'yandex','track_id'=>$trackId],['authorization'=>'Bearer '.$token]);
  $resolved=json_decode($resp->body,true);
  if($approved){
   if(!$listed || !$mapping || (int)$mapping['replacement_id']!==$e['rid']){
    $summary['issues'][]=['track'=>$trackId,'error'=>'missing_approved_catalogue'];continue;
   }
   $summary['catalogue_present_active']++;
   if($resp->status!==200||($resolved['found']??false)!==true || (int)($resolved['replacement_id']??0)!==$e['rid'] || !isset($resolved['audio_url'])){
     $summary['issues'][]=['track'=>$trackId,'error'=>'approved_resolve_missing'];continue;
   }
   $summary['resolve_found']++;
   $url=parse_url((string)$resolved['audio_url']);
   if(!is_array($url)||!preg_match('~^/api/v1/audio/[1-9][0-9]{0,17}$~D',(string)($url['path']??''))){
     $summary['issues'][]=['track'=>$trackId,'error'=>'invalid_signed_audio_url'];continue;
   }
   parse_str((string)($url['query']??''),$params);
   $head=$app->handle('HEAD',(string)$url['path'],$params);
   $size=$e['size'];
   if($head->status!==200 || ($head->headers['Content-Type']??'')!=='audio/mpeg' ||
      (int)($head->headers['Content-Length']??0)!==$size || ($head->headers['Accept-Ranges']??'')!=='bytes'){
     $summary['issues'][]=['track'=>$trackId,'error'=>'head_failed'];continue;
   }
   $summary['head200']++;
   $part=$app->handle('GET',(string)$url['path'],$params,['range'=>'bytes=0-63']);
   if($part->status!==206 || (int)($part->headers['Content-Length']??0)!==64 ||
      ($part->headers['Content-Range']??'')!=='bytes 0-63/'.$size){
     $summary['issues'][]=['track'=>$trackId,'error'=>'range_header_failed'];continue;
   }
   ob_start();$part->emitBody();$audio=ob_get_clean();
   $stream=$store->openStream((string)$r['storage_key']);
   try{$actual=fread($stream,64);}finally{fclose($stream);}
   if(!is_string($audio)||strlen($audio)!==64||$audio!==$actual){
     $summary['issues'][]=['track'=>$trackId,'error'=>'range_audio_bytes_mismatch'];continue;
   }
   $summary['range206']++;
  }else{
   if($listed || $mapping){
    $summary['issues'][]=['track'=>$trackId,'error'=>'inactive_visible_in_catalogue'];continue;
   }
   $summary['catalogue_correctly_absent_inactive']++;
   if($resp->status!==200 || ($resolved['found']??null)!==false){
    $summary['issues'][]=['track'=>$trackId,'error'=>'inactive_resolve_leaks'];continue;
   }
   $summary['resolve_not_found_inactive']++;
  }
 }
 $n=$summary['approved_active'];$inactive=$summary['pending']+$summary['rejected']+$summary['disabled'];
 $summary['pass']=$summary['checked']===100 &&
   $summary['batch1']['total']===50 && $summary['batch2']['total']===50 &&
   $n+$inactive===100 && $summary['asset_verified']===100 &&
   $summary['catalogue_present_active']===$n &&
   $summary['catalogue_correctly_absent_inactive']===$inactive &&
   $summary['resolve_found']===$n && $summary['head200']===$n && $summary['range206']===$n &&
   $summary['resolve_not_found_inactive']===$inactive && !$summary['issues'] &&
   !$summary['missing'] && !$summary['duplicate_versions'];
 echo json_encode($summary,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR),"\n";
 if(!$summary['pass'])exit(1);
}catch(Throwable $e){
 fwrite(STDERR,'CELIKOM_READONLY_ERROR: '.get_class($e).': '.$e->getMessage()."\n");exit(2);
}
