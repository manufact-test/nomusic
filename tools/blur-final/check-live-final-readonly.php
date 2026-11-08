<?php
declare(strict_types=1);
/** Independent immutable read-only production audit for the 200 pinned CELIKOM pending songs.
 * Read-only MySQL, private audio SHA256 & pinned Git blob digest, catalog and resolve.
 * Runs via SSH stdin; does not create staging files or modify production state.
 */
if(PHP_SAPI!=='cli'||count($argv)!==1)exit(2);
ini_set('display_errors','0');
$base='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
$expected=[
  '108127271'=>['size'=>5989997,'duration_ms'=>149107,'blob'=>'0646801d0d6bdb80c0f3da92c47238d73eb40c7e'],
  '48592062'=>['size'=>8374274,'duration_ms'=>207203,'blob'=>'3d79f177ed756b1973a1b9386a46e289f5800472'],
  '83836721'=>['size'=>5379597,'duration_ms'=>132336,'blob'=>'73353c092a2c7d872ee41033b2ac1818ee028e67'],
  '61843247'=>['size'=>8660968,'duration_ms'=>208483,'blob'=>'cc84f3ba1a80a5e58ba4cc8f5c401a6d8ccbea35'],
  '119057929'=>['size'=>6503238,'duration_ms'=>162168,'blob'=>'2c6cadb681047910bbd3fce7c9dcf208c30be375'],
  '119057918'=>['size'=>5492822,'duration_ms'=>136908,'blob'=>'67ba2b9392e095253b81a2cb71aeea19359da4e2'],
  '83836719'=>['size'=>6850813,'duration_ms'=>169117,'blob'=>'feef0b4265cbd26c3fe19bfd964908d76a185211'],
  '61843270'=>['size'=>13685491,'duration_ms'=>339984,'blob'=>'ded1bc4383daecb2aafc32b165fb70b16dccb088'],
  '104242352'=>['size'=>5524845,'duration_ms'=>133355,'blob'=>'2c40cc62a47ccb47a9b1450e59e4afe42d79d4a6'],
  '104242335'=>['size'=>5727749,'duration_ms'=>138423,'blob'=>'c4f18a97fbbe67753d7cff0cb51d59e45248559d'],
  '130919931'=>['size'=>4614251,'duration_ms'=>115174,'blob'=>'d2aba9a97c221110b39945533513c95e75ca9be7'],
  '131898097'=>['size'=>6249182,'duration_ms'=>153078,'blob'=>'e6f21f233ee69a1ee26fb21790d57c2fdade8e3f'],
  '130919969'=>['size'=>5079230,'duration_ms'=>126798,'blob'=>'8032df0afb27fd5478c9dbe6e6c7264b60d598ee'],
  '36063273'=>['size'=>7480866,'duration_ms'=>184842,'blob'=>'1d253bf605832c452eb849334acaae583e9c604c'],
  '152439616'=>['size'=>6067223,'duration_ms'=>150909,'blob'=>'02109b318e2e18f27155d7266be856be56908d03'],
  '124469828'=>['size'=>5595347,'duration_ms'=>139624,'blob'=>'7294ebd67087e5f530ce0ee3b53e707e8667e537'],
  '148716984'=>['size'=>7435956,'duration_ms'=>183745,'blob'=>'044a37a088cdcbcd5d35063cf8d245afbb249353'],
  '124469833'=>['size'=>4315347,'duration_ms'=>107624,'blob'=>'10a3ad30a72ab6a647bdd3fac8356f72583a4f22'],
  '148716115'=>['size'=>6478286,'duration_ms'=>161698,'blob'=>'58f6b18571eaa51503a4b79c1a66fa87fc1e4b36'],
  '124469850'=>['size'=>5822090,'duration_ms'=>145293,'blob'=>'6d3800b2978da6e06d1094fd286f246bbd789b6a'],
  '148716980'=>['size'=>5928168,'duration_ms'=>146051,'blob'=>'52f38ed8ebbfa88bc3b3e440f45878ba2f973e37'],
  '148716970'=>['size'=>6614666,'duration_ms'=>163213,'blob'=>'b688a004c0b41f861a2f5d0c4bf5ed28bd4cb472'],
  '134575495'=>['size'=>4815978,'duration_ms'=>120294,'blob'=>'a543c2b77ace395611cdecf7441a92848fe704b6'],
  '119454084'=>['size'=>3432724,'duration_ms'=>84062,'blob'=>'8d803843a0dfb1a7f11c7e34b058fe903e6a5120'],
  '143243403'=>['size'=>4124212,'duration_ms'=>103105,'blob'=>'df45ea59dd3b460f5c7664da12542747cb7eb7fe'],
  '135962521'=>['size'=>4130839,'duration_ms'=>102269,'blob'=>'8426eb19815d3469fc63e5221586384df89cf97b'],
  '132599811'=>['size'=>3594555,'duration_ms'=>89260,'blob'=>'32a1db3bc23a579fd600278cf625b5a195715ff0'],
  '132335086'=>['size'=>4158737,'duration_ms'=>103863,'blob'=>'b514f4836fbc53e07058e8331c3119ab3727c266'],
  '138562764'=>['size'=>4453942,'duration_ms'=>110629,'blob'=>'613e45304497905084934e3038dcec20bc2774cf'],
  '138562775'=>['size'=>4642024,'duration_ms'=>115331,'blob'=>'2751dbac9ebd54199b3b8a12ef541cf551053f6f'],
  '138562767'=>['size'=>5218808,'duration_ms'=>129750,'blob'=>'8f25a57a17c1c71913dbf2eccd982096099ffe2f'],
  '137834249'=>['size'=>4960365,'duration_ms'=>124008,'blob'=>'56ebc62d330c3a01f8396b5dcea344798e58062b'],
  '148716953'=>['size'=>6503907,'duration_ms'=>160444,'blob'=>'e4b81655d7af69fa195cb63602378abdd5d003c7'],
  '147651927'=>['size'=>3451342,'duration_ms'=>86178,'blob'=>'04997fbc56289b48870fe26db715fafe25c32c3b'],
  '123291813'=>['size'=>4594260,'duration_ms'=>113006,'blob'=>'9635ccb85ec8012ee8d44229b45195f4c4d99021'],
  '141111615'=>['size'=>3190744,'duration_ms'=>77871,'blob'=>'0f29c711f5422c35c7f276c0169458e2a3d7d572'],
  '36142286'=>['size'=>6307900,'duration_ms'=>148402,'blob'=>'6cb2c056f61d8f404ab859dfb3c7697e8780226a'],
  '138494971'=>['size'=>4937284,'duration_ms'=>119327,'blob'=>'54beed890c99627cd9215a9adefd60872f6e124c'],
  '126980904'=>['size'=>4477387,'duration_ms'=>111935,'blob'=>'95d1d941bc2c55e38c5ef99fe14f4b56acfd4eb9'],
  '132909312'=>['size'=>6435526,'duration_ms'=>160888,'blob'=>'a92c082b039a487791e143d1636f946fd9763a51'],
  '144991744'=>['size'=>5217175,'duration_ms'=>130429,'blob'=>'8a84897963e04c11720aee546591bd9e7509449f'],
  '36161933'=>['size'=>9073311,'duration_ms'=>224679,'blob'=>'f99953a73c49d8e4b57c70fd0f23772b8199ccd6'],
  '134699699'=>['size'=>5062957,'duration_ms'=>126302,'blob'=>'68add3e26489d7df24dab08e95ad61584fb04fce'],
  '118251364'=>['size'=>6339126,'duration_ms'=>157989,'blob'=>'0e261645715ae84e7b8bf78f1cf6a73dd7e2041f'],
  '134699697'=>['size'=>7951697,'duration_ms'=>198661,'blob'=>'8c0796d76c7b93d6d3e9c40d661f854724b22eaf'],
  '111618481'=>['size'=>5486194,'duration_ms'=>134452,'blob'=>'c91c0dda6ff255f976786c182c5883c9feaf17bd'],
  '137240585'=>['size'=>6348698,'duration_ms'=>158433,'blob'=>'0330299dd7d0fd1c9d5b7b3af528aecdfb2a411e'],
  '118251363'=>['size'=>6943077,'duration_ms'=>173087,'blob'=>'15caf6564595e12c2bd9572ff35f3f77d1bc06c2'],
  '118618030'=>['size'=>5349566,'duration_ms'=>133198,'blob'=>'83d58c84b65229c528d881e3b3d16a235114e826'],
  '45239756'=>['size'=>7697159,'duration_ms'=>190250,'blob'=>'8519472218057c9636e058b017c0e116a3284d72'],
  '133041135'=>['size'=>5415541,'duration_ms'=>135027,'blob'=>'f3a1cdcf234851ff6634b48799e22777b67aaa1a'],
  '113140423'=>['size'=>7241041,'duration_ms'=>180741,'blob'=>'5515afe40c0b265040781a92a353e208d4814e03'],
  '93012505'=>['size'=>5289735,'duration_ms'=>130090,'blob'=>'0d9a8cb26ce03e0de1bb991e68e0b086cfbafc41'],
  '83371036'=>['size'=>5189425,'duration_ms'=>127582,'blob'=>'e1ef0ec271f10c1472699c60f9aa47e3f94482e3'],
  '70975546'=>['size'=>9495450,'duration_ms'=>235233,'blob'=>'4ce23e96e703453bfef6da14d95f4ad1fb35c647'],
  '93012514'=>['size'=>7705540,'duration_ms'=>190485,'blob'=>'54b4af45be2a7e04aabd0711e8e88f38a3460f8b'],
  '70975550'=>['size'=>10037752,'duration_ms'=>248790,'blob'=>'6ccd4611cedfdae7038e591981cd8b636c02e71f'],
  '42832397'=>['size'=>7289648,'duration_ms'=>180062,'blob'=>'26c725e081bb76e2dd609d2462d61bb779c38f99'],
  '48592130'=>['size'=>12507869,'duration_ms'=>310518,'blob'=>'c67d04b3f9237c1ae4c6b0262622ad372dbf6485'],
  '59933963'=>['size'=>9622906,'duration_ms'=>238393,'blob'=>'af068eeb9e567fb82a5ab07090ce5736c5c7af55'],
  '109301175'=>['size'=>10288506,'duration_ms'=>255033,'blob'=>'14c5679ab65337696676638bca6f15257b103fd8'],
  '42832398'=>['size'=>6487188,'duration_ms'=>160026,'blob'=>'64fa0cdd4e0a5c56464d435283bee7c8744fce68'],
  '150669894'=>['size'=>8622611,'duration_ms'=>204565,'blob'=>'30286bff4ce852dd3e15c4121efd79a67197e0cb'],
  '150669900'=>['size'=>7127857,'duration_ms'=>177502,'blob'=>'16103383558c069cc0661a224d81d59fc62bf8ce'],
  '57185852'=>['size'=>5636642,'duration_ms'=>138762,'blob'=>'8028cc648346c06c4f5af229a15e8221faf7b15f'],
  '59933949'=>['size'=>10527809,'duration_ms'=>261042,'blob'=>'79e4d2f6333b0b86085ef745b2710c05515dad77'],
  '53590445'=>['size'=>8831940,'duration_ms'=>218645,'blob'=>'96cd0fa4a9190843582986ed3faad2ebd578c946'],
  '43900345'=>['size'=>6356576,'duration_ms'=>156761,'blob'=>'de56fded1bcfe168833f3bb8ff4bced00f6b4465'],
  '53586396'=>['size'=>4479939,'duration_ms'=>109845,'blob'=>'56fe48d564cc354d47180285f32714f3fc992b69'],
  '53582342'=>['size'=>9765659,'duration_ms'=>244036,'blob'=>'a5f7dc94aadff710fa581354df72e6c32b8d0d36'],
  '63740136'=>['size'=>6485099,'duration_ms'=>159974,'blob'=>'081e3c7a8d67fa605c562a53cd7e22a30e3bf1b1'],
  '36063262'=>['size'=>7837176,'duration_ms'=>193750,'blob'=>'c7e4720ba362e287e373820532addb133ba977de'],
  '36063267'=>['size'=>5208212,'duration_ms'=>128026,'blob'=>'4954fa28d8c8fc6d492a8ea340debcc79d2989fa'],
  '36063272'=>['size'=>6740033,'duration_ms'=>166322,'blob'=>'b3e3f0436536f98491ee02aa80bf1308856965d5'],
  '53685454'=>['size'=>8171703,'duration_ms'=>200882,'blob'=>'9d6ea1f9f049ffda3cdddc4e79d103fae1027481'],
  '148716143'=>['size'=>5744892,'duration_ms'=>143517,'blob'=>'2c0d27e4fec896d43c25c314f0f4bbc34af26080'],
  '29852766'=>['size'=>6163268,'duration_ms'=>152059,'blob'=>'a22bd4b50469d2290a084dfdfc19223a3703f7a4'],
  '148716127'=>['size'=>4682106,'duration_ms'=>116793,'blob'=>'471d00e6699efd2424add36cd71884f67b029384'],
  '63740184'=>['size'=>8015874,'duration_ms'=>198243,'blob'=>'08eab050e12dd68013d64c0881d05a4cc2d3d307'],
  '79405443'=>['size'=>6576005,'duration_ms'=>162247,'blob'=>'baeacba660c0f5f6c3acc3fb5c7b84df450cf3a7'],
  '148715965'=>['size'=>6534209,'duration_ms'=>161202,'blob'=>'9e21c35fe3d9cd598de109846266c45bea853604'],
  '148716969'=>['size'=>5847711,'duration_ms'=>144039,'blob'=>'4175621fe8c5ef91e3f5ad4c3eabab55aec01081'],
  '124469853'=>['size'=>4779282,'duration_ms'=>119223,'blob'=>'562be4df457617c220b15e6d64dd03ab073b009d'],
  '93570845'=>['size'=>6400462,'duration_ms'=>157858,'blob'=>'998ccb22f8d4aceae35f8582d6a2e3634e9a2b27'],
  '109918674'=>['size'=>8062476,'duration_ms'=>201456,'blob'=>'dca7a975abf6e8e956671bd5b2267391fff7709f'],
  '105844299'=>['size'=>8142440,'duration_ms'=>200385,'blob'=>'f01fb6b0be6e029dbc943a0b80a787f3eec2c97c'],
  '110945082'=>['size'=>4634166,'duration_ms'=>115749,'blob'=>'7e3d395350acf2bf829935c7007fa0dd3293d787'],
  '76780022'=>['size'=>5751301,'duration_ms'=>143752,'blob'=>'870621df46c5f23753a8d28f761c9d83173a9ddc'],
  '110945083'=>['size'=>3958803,'duration_ms'=>97097,'blob'=>'b8391776a081019e1c8ae14fb9e7795a61ada624'],
  '110945084'=>['size'=>5913014,'duration_ms'=>144771,'blob'=>'b82389cb61eb3488d9bb62e500a0782e069166ac'],
  '110945087'=>['size'=>5231847,'duration_ms'=>130691,'blob'=>'4f1f4d7b3dcb0d15d9a28f31939e05a17637c0ea'],
  '110945088'=>['size'=>5648403,'duration_ms'=>138162,'blob'=>'df02b00939a12e6fb98abcea750910ae0d5312d6'],
  '110945085'=>['size'=>4882781,'duration_ms'=>119040,'blob'=>'38356a9fe9a8f13b62fee4480be792b2727d2cd3'],
  '110945092'=>['size'=>7466238,'duration_ms'=>183562,'blob'=>'46931008b096cd5a353ea92ac5faa4e865a92e36'],
  '110945091'=>['size'=>5464323,'duration_ms'=>133564,'blob'=>'b595ac7a20cf05e20bd33a401e2c9553da467bf2'],
  '110945093'=>['size'=>4610551,'duration_ms'=>113110,'blob'=>'1509085dd22bd670eab87c31f23490fcd942d655'],
  '119689460'=>['size'=>4467294,'duration_ms'=>110838,'blob'=>'2aa09cdc2a8e2f2e41bd529f44f10fb03cd87d53'],
  '119689461'=>['size'=>5723261,'duration_ms'=>142237,'blob'=>'5a30dae074e3ff83c123616d1d4858fe453278b0'],
  '119689464'=>['size'=>5634445,'duration_ms'=>140016,'blob'=>'09f3c9521df1f71a3d84103da306b119bb6645ee'],
  '126984723'=>['size'=>5199405,'duration_ms'=>129984,'blob'=>'bd67a75379023f3bdb606a984ba1ffe84523db43'],
  '136797648'=>['size'=>5740669,'duration_ms'=>143517,'blob'=>'32d108ff6a6b54071481d142627248af920f21d1'],
  '39193875'=>['size'=>7160685,'duration_ms'=>179017,'blob'=>'6ab0eb4cea167e7a97d3ff52b8ae5e77a8b9cd26'],
  '36045842'=>['size'=>9677889,'duration_ms'=>239935,'blob'=>'08cc3e48705c2f7259413b0067b779d0449ea342'],
  '39580298'=>['size'=>6645167,'duration_ms'=>164206,'blob'=>'d7270f85e2233829d96410195ee58dd7eee166cf'],
  '34972342'=>['size'=>11039212,'duration_ms'=>274730,'blob'=>'17a84f1e5aab0dbdb8e93347ecad417838dbad1e'],
  '37231301'=>['size'=>9300996,'duration_ms'=>228493,'blob'=>'e9386e6af28268d9e4aae1ad83ef07eae755c4f0'],
  '37231311'=>['size'=>5404256,'duration_ms'=>135001,'blob'=>'ad54713b63975b9502c3035676b0f3c06f53c093'],
  '44803091'=>['size'=>10274599,'duration_ms'=>249469,'blob'=>'9812559838c01aa05f55c62a758b6daff794b91f'],
  '59397779'=>['size'=>8269366,'duration_ms'=>206629,'blob'=>'ae31780b8d523f83e0cef37ce755df9d98fd448a'],
  '71650516'=>['size'=>8296002,'duration_ms'=>205218,'blob'=>'d82cbff9120d9c86df4348539e41abf46e671f1a'],
  '70748121'=>['size'=>3650873,'duration_ms'=>91272,'blob'=>'09304253c230f77f6629ed444bbe57e6a9f4b397'],
  '36360202'=>['size'=>7551939,'duration_ms'=>186645,'blob'=>'be497bbd5810ca8a4dcfe3c4d6dff9c85421d29e'],
  '36620592'=>['size'=>6619473,'duration_ms'=>165381,'blob'=>'79326c624799f0f64085d36ce1a15dd61fe5565b'],
  '58746554'=>['size'=>8713447,'duration_ms'=>217731,'blob'=>'f47b4bdfbdc0488eeae7ca93611b0ca4f7abfecd'],
  '130751224'=>['size'=>5146859,'duration_ms'=>128026,'blob'=>'0cbd7bd0224496c6a6ce9d018f8ea1db7424afda'],
  '119351895'=>['size'=>4499330,'duration_ms'=>112483,'blob'=>'744235628a2d56eb752a71c946f4b9539de7dadf'],
  '132217704'=>['size'=>5796049,'duration_ms'=>144901,'blob'=>'6e164603f990fe0ea5c8a0ee98f07e4d681ad75f'],
  '27737513'=>['size'=>6997971,'duration_ms'=>169117,'blob'=>'726fdfa2678625e2e7402b135bb495d6d1436d35'],
];
$pdo=null;
try{
    if(count($expected)!==118)throw new RuntimeException('wrong_plan_length');
    $rel=realpath($base.'/current');
    if(!is_link($base.'/current')||!$rel||!str_starts_with($rel,$base.'/releases/'))
       throw new RuntimeException('unsafe_active_release');
    require_once $rel.'/bootstrap.php';
    $cfg=require $rel.'/config/app.php';
    if(($cfg['environment']??'')!=='production'||($cfg['storage_driver']??'')!=='local'
       ||realpath((string)$cfg['storage_path'])!==$base.'/shared/audio')
       throw new RuntimeException('unexpected_live_storage');
    $pdo=\Celikom\Database\Connection::open($cfg);
    $store=new \Celikom\Storage\LocalStorageAdapter($cfg['storage_path']);
    $catalogue=(new \Celikom\Application\ReplacementCatalogueService($pdo))->snapshot();
    $inCatalogue=[];
    foreach(($catalogue['tracks']??[]) as $row)$inCatalogue[(string)$row['track_id']]=true;
    $lookup=new \Celikom\Repositories\PdoCatalogRepository($pdo);
    $app=new \Celikom\Application($cfg);
    $token=(string)($cfg['test_api_token']??'');
    if(strlen($token)<24)throw new RuntimeException('read_only_api_token_unavailable');
    $q=$pdo->prepare("SELECT r.id,r.status,r.is_active,r.approved_at,r.approved_by_admin_id,r.disabled_at,
          a.storage_driver,a.storage_key,a.sha256,a.size_bytes,a.mime_type,a.duration_ms
        FROM tracks t JOIN track_replacements r ON r.track_id=t.id
        JOIN audio_assets a ON a.id=r.audio_asset_id
        WHERE t.service='yandex' AND t.service_track_id=? ORDER BY r.id");
    $verified=0;$absent=0;$catalogueAbsent=0;$bytes=0;$issues=[];$batch=[0,0,0];$ids=[];$ordinal=0;
    $pdo->exec('START TRANSACTION READ ONLY');
    foreach($expected as $id=>$e){
        $slot=intdiv($ordinal++,50);
        $id=(string)$id;
        $q->execute([$id]);$rows=$q->fetchAll(PDO::FETCH_ASSOC);
        if(count($rows)!==1){$issues[]=['id'=>$id,'reason'=>'missing_or_multiple_versions'];continue;}
        $r=$rows[0];
        if($r['status']!=='pending'||(int)$r['is_active']!==0||$r['approved_at']!==null
           ||$r['approved_by_admin_id']!==null||$r['disabled_at']!==null){
           $issues[]=['id'=>$id,'reason'=>'not_unapproved_pending'];continue;
        }
        if(isset($inCatalogue[$id])||$lookup->findActive('yandex',$id)!==null){
           $issues[]=['id'=>$id,'reason'=>'pending_is_public'];continue;
        }
        $catalogueAbsent++;
        if($r['storage_driver']!=='local'||$r['mime_type']!=='audio/mpeg'
           ||(int)$r['size_bytes']!==$e['size']
           ||abs((int)$r['duration_ms']-$e['duration_ms'])>1500
           ||!$store->exists((string)$r['storage_key'])
           ||$store->getSize((string)$r['storage_key'])!==$e['size']
           ||$store->getMimeType((string)$r['storage_key'])!=='audio/mpeg'){
           $issues[]=['id'=>$id,'reason'=>'private_asset_invalid'];continue;
        }
        $fp=$store->openStream((string)$r['storage_key']);
        try{
            $sha1=hash_init('sha1');hash_update($sha1,'blob '.$e['size']."\0");
            $sha256=hash_init('sha256');
            while(!feof($fp)){
                $chunk=fread($fp,262144);
                if($chunk===false)throw new RuntimeException('file_unreadable_'.$id);
                if($chunk!==''){hash_update($sha1,$chunk);hash_update($sha256,$chunk);}
            }
            $blob=hash_final($sha1);$digest=hash_final($sha256);
        }finally{fclose($fp);}
        if(!hash_equals($e['blob'],$blob)||!hash_equals((string)$r['sha256'],$digest)){
            $issues[]=['id'=>$id,'reason'=>'private_audio_digest_or_source_mismatch'];continue;
        }
        $verified++;$bytes+=$e['size'];
        $resp=$app->handle('GET','/api/v1/resolve',['service'=>'yandex','track_id'=>$id],['authorization'=>'Bearer '.$token]);
        $data=json_decode($resp->body,true);
        if($resp->status===200 && ($data['found']??null)===false){$absent++;}else{
            $issues[]=['id'=>$id,'reason'=>'pending_api_resolve_visible'];
        }
        $batch[$slot]++;
        $ids[]=['track_id'=>$id,'replacement_id'=>(int)$r['id']];
    }
    $pdo->rollBack();
    $pass=count($expected)===118 && $verified===118 && $absent===118
          && $batch===[50,50,18] && !$issues;
    $out=['status'=>'FINAL118_INDEPENDENT_READONLY','pass'=>$pass,'checked'=>118,
          'pending'=>$verified,'files_verified'=>$verified,'private_bytes'=>$bytes,
          'batch_counts'=>$batch,'catalogue_absent'=>$catalogueAbsent,
          'resolve_not_found'=>$absent,'auto_approved'=>0,'active'=>0,
          'writes'=>0,'issues'=>$issues,'records'=>$ids];
    echo json_encode($out,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
    if(!$pass)exit(1);
}catch(Throwable $e){
    if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,'LIVE200_INDEPENDENT_AUDIT_REFUSED: '.$e->getMessage()."\n");
    exit(2);
}
