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
  '112679398'=>['size'=>7266264,'duration_ms'=>181551,'blob'=>'7bd6b6576d8e81ccac27a4a3a14d04621baab670'],
  '142267453'=>['size'=>7086187,'duration_ms'=>176614,'blob'=>'209582cfecaeca011df5a74fa94f7d5f29059e9b'],
  '118841471'=>['size'=>6428820,'duration_ms'=>160026,'blob'=>'f3c41bdfe05cbaed863ea191b82d12f1ec76d71e'],
  '81747393'=>['size'=>8867466,'duration_ms'=>219533,'blob'=>'97b2a4b2f949e8f9780308f4b55b2c789d48c82b'],
  '85327088'=>['size'=>3421204,'duration_ms'=>142550,'blob'=>'bc462d679bafabb4c6bb20477e1dcca0f97f9a39'],
  '116649710'=>['size'=>4055147,'duration_ms'=>101094,'blob'=>'71ec1e838d0feab9356a4b2ee056ab7a75f47708'],
  '44121115'=>['size'=>7660580,'duration_ms'=>186723,'blob'=>'eff2951340ea312b0bc4a9f8eb18ec2057b46a42'],
  '138503834'=>['size'=>5485698,'duration_ms'=>135027,'blob'=>'cc5cdccdeb4c306a38b359e9313f1a2a26f27801'],
  '118111184'=>['size'=>6054559,'duration_ms'=>150439,'blob'=>'e7c93b2e09cac9f9c53b4aaa518b7b745fc15f1c'],
  '55928194'=>['size'=>8043021,'duration_ms'=>198896,'blob'=>'95bbb75bbef291bfdbe481ee6d50b2019c11f429'],
  '137240582'=>['size'=>5898347,'duration_ms'=>147174,'blob'=>'3637e453d2e87f0091b2898cb9cfbaa4a9b75e61'],
  '97277432'=>['size'=>3745736,'duration_ms'=>154410,'blob'=>'0ef0e21f073c0cea6674210e0c77f0c91d4bb30a'],
  '103844893'=>['size'=>5501797,'duration_ms'=>136647,'blob'=>'2546d2c9c087b653a3ce22107d86ccd1829a8984'],
  '97277434'=>['size'=>5790429,'duration_ms'=>137195,'blob'=>'56cceaa1d2b56454ac0f961c4208dd7d52c256f0'],
  '39779900'=>['size'=>4408030,'duration_ms'=>180036,'blob'=>'15a05f813201b7293cad11d68aef373fb6693670'],
  '119296543'=>['size'=>8048891,'duration_ms'=>201117,'blob'=>'144f16c75d3f1d946e91702d8641b39320a5377a'],
  '109125971'=>['size'=>5829530,'duration_ms'=>145633,'blob'=>'5ffd165235d8be8ec9c3e4aa46408897ad91fff4'],
  '91519009'=>['size'=>5502894,'duration_ms'=>135419,'blob'=>'de02f969b851df0146061fae5713f1553c72c518'],
  '100717938'=>['size'=>6616755,'duration_ms'=>163265,'blob'=>'24421fb698867ebdb37bd955c757d4b4967c5cae'],
  '41900814'=>['size'=>11948848,'duration_ms'=>296542,'blob'=>'2756138085cef581c44b720738824f5224fa3336'],
  '118990563'=>['size'=>5349921,'duration_ms'=>133642,'blob'=>'59df10b6f37240f3698d102d54a0c460c06d76a4'],
  '78871330'=>['size'=>8310535,'duration_ms'=>205610,'blob'=>'401978625fcc6fcb1d27f1e00a0391765aabac90'],
  '66668866'=>['size'=>5135508,'duration_ms'=>210390,'blob'=>'fc1068e5a672b7a829880aa6fa729ebcd98e48ff'],
  '125535665'=>['size'=>4671866,'duration_ms'=>115513,'blob'=>'41394f98fbf0b040998d7ae85b9b12d219187c4e'],
  '131393823'=>['size'=>7247644,'duration_ms'=>180036,'blob'=>'08d033136037ed13f0c23c8901a8bb8542c01e2a'],
  '144973122'=>['size'=>5079873,'duration_ms'=>125283,'blob'=>'19d8384bbbc1bc8709319436f88a312553a56236'],
  '65889392'=>['size'=>7109948,'duration_ms'=>175595,'blob'=>'535f46543c73b349d6ad40fd84bd7be03a0f1787'],
  '137242382'=>['size'=>5932974,'duration_ms'=>148219,'blob'=>'2006a81e90dd5f4c7ea624570b66e9d41f6c511e'],
  '40345287'=>['size'=>3579217,'duration_ms'=>145502,'blob'=>'bea25268a9d38226da03bee2f305b3a4ae96dddb'],
  '48591615'=>['size'=>12453556,'duration_ms'=>309185,'blob'=>'7d62b08d2485f6f950c1211216d6315fb6aa3758'],
  '145192521'=>['size'=>7699266,'duration_ms'=>186462,'blob'=>'5e399cdbb338205f1fa50749377df23b520c9ed1'],
  '145192522'=>['size'=>8089895,'duration_ms'=>201169,'blob'=>'82539e0b909a0d8625ee401ff03ca41e6a3f0f6f'],
  '106713246'=>['size'=>8129768,'duration_ms'=>201091,'blob'=>'3734f0d6cca1ffe40ea4ed9b2afe5711224bc77c'],
  '40345286'=>['size'=>4688271,'duration_ms'=>191713,'blob'=>'04a3068b893a1679994b3a2f87fa24ecd116ebe9'],
  '108021210'=>['size'=>5428707,'duration_ms'=>133564,'blob'=>'a6578c374d31619f94fbd32ce846409a3c99a635'],
  '61221104'=>['size'=>8777605,'duration_ms'=>217287,'blob'=>'f7cfdfd1eb30bb3b8af6c3fe80603cb1faa2446e'],
  '111402813'=>['size'=>5641866,'duration_ms'=>138893,'blob'=>'c47be37f96feb88b314364a04e7bea013cabda06'],
  '138756210'=>['size'=>7026983,'duration_ms'=>175569,'blob'=>'9afcd8cf056ca5a0b3fdfc121e7c7da104e01562'],
  '45439389'=>['size'=>9909229,'duration_ms'=>245577,'blob'=>'6d83b80364488c1da0cf3044fa83a267de33cb07'],
  '103247540'=>['size'=>4098552,'duration_ms'=>100310,'blob'=>'4866ac83e247ece7b0d7010a46daeb16e1633da0'],
  '117219736'=>['size'=>8877288,'duration_ms'=>221571,'blob'=>'abb56e31131b246102989e485421905e5ac79e37'],
  '117219721'=>['size'=>16256357,'duration_ms'=>406047,'blob'=>'18833978c3a227e7cc088d9a56422951d5a74255'],
  '58478014'=>['size'=>7528931,'duration_ms'=>186044,'blob'=>'b6eece3bac8f1c65b5210c9f9b568f7d04939578'],
  '95699208'=>['size'=>5385866,'duration_ms'=>132493,'blob'=>'3f9c9f0926e011e581f451cb35e13ad3b5b43d08'],
  '86503267'=>['size'=>5236446,'duration_ms'=>128758,'blob'=>'41f33f501dbfd213ab7fd9af34b9132ad7dd001e'],
  '95699209'=>['size'=>4119450,'duration_ms'=>100833,'blob'=>'5068bf2c3c45b65ccfb67db686c8b81525d7ecea'],
  '61638510'=>['size'=>8047221,'duration_ms'=>199027,'blob'=>'0af83d4245d6750b3d1eb0fe8d910a6afc7ace34'],
  '107604519'=>['size'=>5949066,'duration_ms'=>146573,'blob'=>'4e93a2ed3f3772518490471d2374641a15debb92'],
  '116649705'=>['size'=>4496094,'duration_ms'=>112118,'blob'=>'92fa8e3c985ad8036ca5319a17cfc5ecc73b29f9'],
  '126242675'=>['size'=>7164220,'duration_ms'=>178155,'blob'=>'a349306b3414e627211ec8e4e774613dba251034'],
  '116649701'=>['size'=>5783408,'duration_ms'=>144300,'blob'=>'ff4dd44ad2bf78015fd23799a397150296058ba3'],
  '119296535'=>['size'=>5558274,'duration_ms'=>136803,'blob'=>'b2803edf3099bc3aef672c653594d88cc0b0fef8'],
  '116649697'=>['size'=>6219130,'duration_ms'=>155193,'blob'=>'6c11c7a743fd2542414401d65eb4d6d7c3de19cf'],
  '63607800'=>['size'=>8549816,'duration_ms'=>211592,'blob'=>'ac47913d87188e9eb2e882c2bc5e74dbbddd5bba'],
  '105382853'=>['size'=>4286260,'duration_ms'=>107154,'blob'=>'df0dcc4e62a76cceedad8e28288c841e7bfcfa9b'],
  '85971524'=>['size'=>4100642,'duration_ms'=>100362,'blob'=>'96ef7e115249b01aa6015012b94211a2eb3d4ce5'],
  '119296520'=>['size'=>8316784,'duration_ms'=>205740,'blob'=>'8b59cdfbd17eac51436646ccac0002b397708135'],
  '105382835'=>['size'=>6586454,'duration_ms'=>162508,'blob'=>'362c20b6547280197f5fe5abe19d02899465f80e'],
  '148716903'=>['size'=>8299042,'duration_ms'=>205322,'blob'=>'0c37f8707b5a2e80bb30c92c55a7f0cd80537949'],
  '105382845'=>['size'=>5989817,'duration_ms'=>147592,'blob'=>'adc1f86d24c10e4e6556c596683f0dacaccd415d'],
  '148716946'=>['size'=>4967907,'duration_ms'=>122044,'blob'=>'a8155f72b5625cf48fcd94b19dbabfb7754407d8'],
  '148716991'=>['size'=>5041049,'duration_ms'=>123873,'blob'=>'893734d4d12c88a4c2552e4c16a4a4c3d6abda57'],
  '73173762'=>['size'=>3266813,'duration_ms'=>79517,'blob'=>'d712f882c16b31b1fec225b07d0c3eca6f965a81'],
  '99699702'=>['size'=>5162258,'duration_ms'=>126903,'blob'=>'a3559dbb73500f4e0499e2e218aaa3369cafcdc3'],
  '107544286'=>['size'=>6111025,'duration_ms'=>150622,'blob'=>'e32e0602b1978555678dd5ee8260297ff2004a61'],
  '105157817'=>['size'=>4284544,'duration_ms'=>104960,'blob'=>'22e5c7d03e2d4b7b25d97b457fb7d9b850666fc8'],
  '106611749'=>['size'=>4795133,'duration_ms'=>119301,'blob'=>'ccf40b6bda7e97380455085dbae8451a140d8230'],
  '96567683'=>['size'=>5882192,'duration_ms'=>144901,'blob'=>'75168b45b5547e97d30c818fbe8d48ef36926138'],
  '112499902'=>['size'=>4848283,'duration_ms'=>111464,'blob'=>'be9f6535b65c10a3e01196668213dc2e0c11072e'],
  '108797218'=>['size'=>5427662,'duration_ms'=>133538,'blob'=>'754da9cca66239530613c5f5b9cf5c1dea68e307'],
  '58720221'=>['size'=>10005338,'duration_ms'=>247954,'blob'=>'b25372efd7d1e453f654ffe8da88be4e3179ba21'],
  '108484225'=>['size'=>3482192,'duration_ms'=>174106,'blob'=>'fb02d9eec33ef47da82156fbc2bd9f8f0c862126'],
  '63027206'=>['size'=>6052049,'duration_ms'=>151301,'blob'=>'3a17a1e05c555b21887e7a94c93ab589c01c912a'],
  '108484171'=>['size'=>6483591,'duration_ms'=>162090,'blob'=>'b1a714044b5cc024c6dc8389b64daa46caf308ba'],
  '36879977'=>['size'=>9452589,'duration_ms'=>234136,'blob'=>'f374af4a9d79e70a6fde8febfaabb4d94fafa3b3'],
  '50941920'=>['size'=>6451662,'duration_ms'=>159138,'blob'=>'d56ad9cf16e6e026f5425d9a0c80fdba1c88d4f4'],
  '40038183'=>['size'=>7490290,'duration_ms'=>185104,'blob'=>'6d29cc3d847702987fa388cce62651f1ce8db461'],
  '90172225'=>['size'=>6071318,'duration_ms'=>149629,'blob'=>'70bf5fd0df88d3cf8a8753a17ff83fce2d742974'],
  '108484207'=>['size'=>9764571,'duration_ms'=>244114,'blob'=>'7f6730d7c7e46fbb8c24b0e7f1234dea735b258c'],
  '128738466'=>['size'=>6130416,'duration_ms'=>153260,'blob'=>'b059a7b3de43b925ee2fc50cb3c63d4b56ba909f'],
  '149171827'=>['size'=>7649115,'duration_ms'=>189074,'blob'=>'e4f648107bca4903516efaaf0411bfc9cdcd619c'],
  '73375313'=>['size'=>7298008,'duration_ms'=>180271,'blob'=>'4c815b8ed9f3c5ddf8500ddc8ab4b9de0d7ac415'],
  '149171825'=>['size'=>8625050,'duration_ms'=>213473,'blob'=>'fdb14fa66553613dfbec8fafd78f16cf5e5d94ef'],
  '53590446'=>['size'=>4244837,'duration_ms'=>103967,'blob'=>'d9cb78a38ec6684f64039a64dae549a63a7fdaf8'],
  '119454076'=>['size'=>4387571,'duration_ms'=>109584,'blob'=>'ba0bbc6dc0d7201f4b5d5cf154c45e59f47c3ad9'],
  '138032099'=>['size'=>5894377,'duration_ms'=>143882,'blob'=>'4ceeb172860e663536adb53d2a391cc7adbc0bd6'],
  '53582343'=>['size'=>10021660,'duration_ms'=>250436,'blob'=>'e5492b42ba551fdc3f42262f9888e4bab38ae380'],
  '146626890'=>['size'=>2295057,'duration_ms'=>138057,'blob'=>'edb7514e8d36ab0599600e9c380032e4839e29ad'],
  '53586382'=>['size'=>12564315,'duration_ms'=>311954,'blob'=>'cc64abc75d82974741c614435f24ed86d6878bda'],
  '108050042'=>['size'=>6634102,'duration_ms'=>165851,'blob'=>'61a1d19ba6ad333cd05c35e609082ba180699934'],
  '45541232'=>['size'=>7453718,'duration_ms'=>184189,'blob'=>'c7dd96b0e5e3fc8228c75b78a0ef938e009cc256'],
  '124889466'=>['size'=>4510868,'duration_ms'=>112666,'blob'=>'1d031816554d6047d14d883e9df04437f2c95a2c'],
  '132344542'=>['size'=>6196907,'duration_ms'=>152320,'blob'=>'f957d755817a0f80e660a6715de84be245aef2a0'],
  '133174434'=>['size'=>4197838,'duration_ms'=>100258,'blob'=>'fe94b7fd3d10f0328e22bf7b63ede9b401539d75'],
  '133174453'=>['size'=>3995128,'duration_ms'=>95190,'blob'=>'f5f95997ed5457c066ca44c6b1c621e5f5ebfc56'],
  '133174448'=>['size'=>5133022,'duration_ms'=>123638,'blob'=>'3d2edeb043d3e37d53532d5de62ed0ada6e3fb0f'],
  '143629775'=>['size'=>4847326,'duration_ms'=>121078,'blob'=>'54b44b1077145ac7f0b237cb5a3bc78bc9e75a59'],
  '55376891'=>['size'=>7998111,'duration_ms'=>197799,'blob'=>'c18cfeb0c62cc1bed218743b5b621eb78de0c279'],
  '41900788'=>['size'=>5594240,'duration_ms'=>137691,'blob'=>'0647d12349408748dd66df0b855acd69ca04c23e'],
  '68074224'=>['size'=>4322996,'duration_ms'=>176536,'blob'=>'de2e66a01f958fed391a260145d8092181d06927'],
  '118415641'=>['size'=>2514024,'duration_ms'=>62851,'blob'=>'d7af6af0dddcbd11a7865ed8209404502126224f'],
  '38976044'=>['size'=>9432735,'duration_ms'=>233639,'blob'=>'26cdd19f6f6af19c98248b48d0ae8ca1efaa69ff'],
  '97495955'=>['size'=>5627237,'duration_ms'=>138527,'blob'=>'e742b18b29f52758d1146fd78a760c19e7634778'],
  '143058948'=>['size'=>1920983,'duration_ms'=>120059,'blob'=>'2aab530ed78277fb6c42c6f4be2c1ba9a823c8b2'],
  '106769378'=>['size'=>5456500,'duration_ms'=>136307,'blob'=>'724999209bf7d7897f0fe90aa5c7a7d725a66103'],
  '134223766'=>['size'=>3875988,'duration_ms'=>96026,'blob'=>'740ee5bbab348d5e4daca3f3f09830bdee8dbb0f'],
  '138041649'=>['size'=>4825383,'duration_ms'=>120529,'blob'=>'2251cbe80b92f31979ce43d8d6eb7c80c244b64b'],
  '38563414'=>['size'=>7851407,'duration_ms'=>196180,'blob'=>'4541d578258d187364d265f9c25f8ea23eb85829'],
  '139307354'=>['size'=>4732342,'duration_ms'=>118309,'blob'=>'f351e7d9a1018a3e8dfffbf5f19862d9af544a73'],
  '143319429'=>['size'=>3201567,'duration_ms'=>80039,'blob'=>'dd2cf9dfd5193e558711227a2ae6ea82402e5cf0'],
  '71766713'=>['size'=>6246841,'duration_ms'=>153992,'blob'=>'1495090cd010a73583aaee23c10e23d0743f6770'],
  '83775793'=>['size'=>6406312,'duration_ms'=>160052,'blob'=>'507fd77690937a128e24854bfe0c21499960aa14'],
  '136904441'=>['size'=>4266318,'duration_ms'=>106658,'blob'=>'d137c5d038ac6469f7154b31e75e70df359fba77'],
  '29720951'=>['size'=>6788098,'duration_ms'=>167523,'blob'=>'a0e126f1bfb21667b3d8b871d365e0c050af1935'],
  '35208794'=>['size'=>10613491,'duration_ms'=>263184,'blob'=>'3ce179d35a842029f5f3381fbd1dff058d0bac59'],
  '75112280'=>['size'=>9289186,'duration_ms'=>232124,'blob'=>'b551cf98622d2f13aa86c3271248e0d866e900b9'],
  '66668868'=>['size'=>4885757,'duration_ms'=>199941,'blob'=>'42e8dac8516bb2e2967334dca408b9a7ddc0e09d'],
  '140701191'=>['size'=>4505644,'duration_ms'=>112536,'blob'=>'3301eba4c2acaf85e5226db4a468bfae4e065642'],
  '48592479'=>['size'=>11307282,'duration_ms'=>280503,'blob'=>'a2cd53323effd5be5b8c52a0a50c8f6458701afd'],
  '29508029'=>['size'=>6716021,'duration_ms'=>165747,'blob'=>'1e1632fa93e9766f1403eb95ff7c2949cccfdf5b'],
  '61221106'=>['size'=>6947988,'duration_ms'=>171546,'blob'=>'47575984a31b1db4b3ef4475d7fe479b13d1da64'],
  '91519011'=>['size'=>4730714,'duration_ms'=>116114,'blob'=>'f1e7935501c5d741ced285aef21bd2744e8b08ea'],
  '29508047'=>['size'=>7125621,'duration_ms'=>175987,'blob'=>'2c3c910dfc1d853d368dc240822d629d5a964b1d'],
  '141012344'=>['size'=>4331871,'duration_ms'=>103732,'blob'=>'c6a5db9d2cf9e6d5e17681f4a64fa1d4a9d67974'],
  '103247537'=>['size'=>5630372,'duration_ms'=>138606,'blob'=>'74a152cc18e69336390cdd4de5ecfa7b5b16e629'],
  '110023293'=>['size'=>3448474,'duration_ms'=>77584,'blob'=>'6339a3911545b7bb5de3c5d84b34ba066796a7d1'],
  '29508038'=>['size'=>7125621,'duration_ms'=>175987,'blob'=>'2c3c910dfc1d853d368dc240822d629d5a964b1d'],
  '113286232'=>['size'=>5837888,'duration_ms'=>145842,'blob'=>'f2dfc327c1f30578207c5b2d4796919351a51ef3'],
  '131393819'=>['size'=>4407379,'duration_ms'=>110184,'blob'=>'bba61393eadc04e65327ba612f942b634011cc86'],
  '131393817'=>['size'=>5544461,'duration_ms'=>137456,'blob'=>'a178dbc41d77d9161980c0dda7d152dc6bb9a31e'],
  '114977973'=>['size'=>5438592,'duration_ms'=>135680,'blob'=>'6b9b1fe6352f450aa86fec0fca8011b890d33461'],
  '125535663'=>['size'=>5676013,'duration_ms'=>140617,'blob'=>'c924e21ae5b9cbb59d395af320f8a50d4e083a93'],
  '133174446'=>['size'=>4735960,'duration_ms'=>113711,'blob'=>'f71b742fd06ec0a59f35c677790985a8a94ed3be'],
  '133174452'=>['size'=>4759993,'duration_ms'=>114312,'blob'=>'652c6778952d5385d0bb3acc1f2465b3d4e7f22c'],
  '135767964'=>['size'=>3761632,'duration_ms'=>94041,'blob'=>'06f95ce4a90d801a40d0c0ed3e619794640bb275'],
  '129925714'=>['size'=>4924604,'duration_ms'=>123115,'blob'=>'f0dea9912e83dc3612d1ef87cc22fd369db32700'],
  '119560551'=>['size'=>5132374,'duration_ms'=>127948,'blob'=>'7783b14f3b70a564bb8a1ce88ea5ef14f4ecb0e0'],
  '59575374'=>['size'=>5639775,'duration_ms'=>138841,'blob'=>'90bee7b1333e367480653cadcd595ae8866c1441'],
  '118366959'=>['size'=>4069877,'duration_ms'=>101747,'blob'=>'a2d85c0ad77d11bd1eaa6bc9574a312aeaf3f61a'],
  '39577642'=>['size'=>5399846,'duration_ms'=>221362,'blob'=>'dfe4b36c2cc5fdc2e91221c9f40bce03038b1bc8'],
  '118366957'=>['size'=>5947329,'duration_ms'=>147905,'blob'=>'3516dea6204564ee9b7e01835f2cdac13c5c81ae'],
  '73447516'=>['size'=>4627270,'duration_ms'=>113528,'blob'=>'1fac947d0a3d2e33cb0d0ffb89a46a86dd0de013'],
  '149218189'=>['size'=>7770553,'duration_ms'=>193672,'blob'=>'c079de5bf26ba80df3906f97c244ace68051c467'],
  '112679389'=>['size'=>6882138,'duration_ms'=>169874,'blob'=>'25468700a608dcf3fbb00113697ece73efb6a00b'],
  '118111189'=>['size'=>7296943,'duration_ms'=>181499,'blob'=>'98953a917ff784c08ad509759290c57b0f9849ef'],
  '53586380'=>['size'=>6437660,'duration_ms'=>160836,'blob'=>'df5d66ed3486224a8b8c56e2546c8b85318a9a84'],
  '102505200'=>['size'=>11911233,'duration_ms'=>295602,'blob'=>'3d3ef11a144afe224c69814e115d2f93367fc5dc'],
  '42976442'=>['size'=>9909229,'duration_ms'=>245577,'blob'=>'49c9d91e41549d2ffb84c5501786cd132a636e6c'],
  '93570844'=>['size'=>5511254,'duration_ms'=>135628,'blob'=>'8ba43f5b3cb3df7e680ffa8bd0c126fd5077d7a2'],
  '152140598'=>['size'=>5732419,'duration_ms'=>143020,'blob'=>'853f5d65e3a2a69f211b1f33ea87bdcf0c884b3f'],
  '36879868'=>['size'=>8949992,'duration_ms'=>221571,'blob'=>'e861a917179a44dd062e34f6c7f32d84b6a8487a'],
  '132020394'=>['size'=>10576564,'duration_ms'=>263105,'blob'=>'24c3303156e24265ae5aca70093890eb1f930df3'],
  '127365608'=>['size'=>5610728,'duration_ms'=>139651,'blob'=>'40bd3d0c1ed838b7e6b86cd2c8e7064d82d99f01'],
  '93556499'=>['size'=>7769257,'duration_ms'=>192052,'blob'=>'02b1d74110bcf9a58164e7f51846f37a2175c27e'],
  '127365607'=>['size'=>5398614,'duration_ms'=>134348,'blob'=>'dfbd2589929108f26aaa4864f1e2d199c9378601'],
  '118618031'=>['size'=>5109240,'duration_ms'=>127190,'blob'=>'cb5a348edbaf029e78fe7ebd1ebe71869f7ddd1c'],
  '113140441'=>['size'=>8119800,'duration_ms'=>202710,'blob'=>'b4f3cbba2fa7f8a6bdf98ebf43a5f4c9698876a9'],
  '118841472'=>['size'=>6317016,'duration_ms'=>157231,'blob'=>'e0a6b5636d09308b7b8b1c0dc412dd71fc007d02'],
  '93556501'=>['size'=>7446405,'duration_ms'=>184007,'blob'=>'eea73903b1f1855c75fce43caec538fd4865913b'],
  '127365611'=>['size'=>6326604,'duration_ms'=>152424,'blob'=>'3b134af4ff6428073d0789fdab254f85d486bf9e'],
  '117131963'=>['size'=>6489571,'duration_ms'=>161724,'blob'=>'d05aa689003989113fe24c117c4e5f4c4f443f13'],
  '119359227'=>['size'=>6631677,'duration_ms'=>165277,'blob'=>'1fd9bed1819fbc9633f3f9c10ce56edd8329c2c3'],
  '119359228'=>['size'=>6994257,'duration_ms'=>174341,'blob'=>'b718732713fd1296e8bc1004555457c47d287793'],
  '119359231'=>['size'=>5780085,'duration_ms'=>143987,'blob'=>'36226d166af231bcc5418bfbaaedee4e062d3ceb'],
  '119359233'=>['size'=>5319285,'duration_ms'=>132467,'blob'=>'5b97c5d002cf5030486369d69bf592e4e6875b8d'],
  '119359232'=>['size'=>5443628,'duration_ms'=>135576,'blob'=>'ba58156c5f4ac7eecb9ec5b3e16576a0ce3e17a2'],
  '119359236'=>['size'=>4789522,'duration_ms'=>119223,'blob'=>'b62e44e13aef0bfb2487206257cc71eda0c7ef89'],
  '59933962'=>['size'=>5207188,'duration_ms'=>128026,'blob'=>'27124c76a1d1b4e65a5b97453f1a7cf5e6794e08'],
  '119359237'=>['size'=>7548280,'duration_ms'=>186122,'blob'=>'0f63e78cf6034cf732c702092dd268e8ab6fa538'],
  '117963715'=>['size'=>6315073,'duration_ms'=>157362,'blob'=>'81d8ebdc7396d2ab1cfee17bf349a672260bf40a'],
  '119280167'=>['size'=>5595702,'duration_ms'=>138789,'blob'=>'90399ee417dd568c714c527d0900a45f77130cf3'],
  '119359239'=>['size'=>8731922,'duration_ms'=>217783,'blob'=>'6e7cd41f839e461e5b9ea45ded83597f73933f15'],
  '119359234'=>['size'=>7133228,'duration_ms'=>177816,'blob'=>'6f6a33bcd69b9ec9d2010625ee45f2a57e74f5fc'],
  '59933959'=>['size'=>5147629,'duration_ms'=>126537,'blob'=>'e0d56b4950982d727f0f5fe86fef09d2a483f926'],
  '131718215'=>['size'=>4732387,'duration_ms'=>118204,'blob'=>'c5237876c75deede4e97ceb3f5265fbedebde900'],
  '131898078'=>['size'=>5908545,'duration_ms'=>144562,'blob'=>'e43bdbf78d124532913b9416e61c524b63e64170'],
  '59933958'=>['size'=>6167450,'duration_ms'=>152033,'blob'=>'722eda7cd4fef7cf1bb954b714972b8461ad5191'],
  '59933939'=>['size'=>7792266,'duration_ms'=>192653,'blob'=>'04ce48b78730357b55b01a800610e43accc02747'],
  '104242351'=>['size'=>3270993,'duration_ms'=>79621,'blob'=>'724f9906ed969218fe873b1a6b3326694c973305'],
  '128253247'=>['size'=>4668199,'duration_ms'=>115043,'blob'=>'b92995995cd3fbc1011eef6b5b20fe3af3e66617'],
  '131898087'=>['size'=>6106031,'duration_ms'=>149499,'blob'=>'08b30c37b3fbd1d30ec7cfcd6f0278cf39e6cb50'],
  '132344559'=>['size'=>4725028,'duration_ms'=>118126,'blob'=>'5acc9443304bbe4676aef4db363739f6b48d2600'],
  '119280173'=>['size'=>5421204,'duration_ms'=>134426,'blob'=>'64f9f1ea2fbb794ed6d166d863ed870c198f2156'],
  '119890674'=>['size'=>5773983,'duration_ms'=>144039,'blob'=>'1ac8fd2563e9dbe584ebdbe48baf8dccc4a285ec'],
  '119454081'=>['size'=>4666514,'duration_ms'=>116663,'blob'=>'0ea0086747fb98d2d6c0676d76f37590a424dfdb'],
  '113990664'=>['size'=>4884858,'duration_ms'=>121913,'blob'=>'388d3a6a72369ac0de7cdd7787029f64ffe32ec4'],
  '97809794'=>['size'=>4902649,'duration_ms'=>121496,'blob'=>'aa69078acd18e533ca89814a93eecc64b5b16954'],
  '138562791'=>['size'=>5135488,'duration_ms'=>128000,'blob'=>'384911bcdd20c724ecdf1deb079d5a106229a0ae'],
  '118366954'=>['size'=>5230551,'duration_ms'=>129985,'blob'=>'45477dbdd0bfecd2bebbf9ba74cbfb49161dbc70'],
  '119890673'=>['size'=>6734244,'duration_ms'=>168046,'blob'=>'861bfc4f37b185a20faff463af2e43f253ef050a'],
  '144098513'=>['size'=>5488644,'duration_ms'=>135784,'blob'=>'ce78a06ccd034b0a06308785c7954f6a70fce986'],
  '45239760'=>['size'=>5728592,'duration_ms'=>141061,'blob'=>'b82faa388cefc3a4af7294b22c186409f2a85ae1'],
  '61693505'=>['size'=>3787151,'duration_ms'=>92500,'blob'=>'2eef2b6bc0ac6b1012ad5cee0a90670b186b88c0'],
  '129501470'=>['size'=>6181577,'duration_ms'=>154331,'blob'=>'70ac51623ddbb3e986f826d13e35ce74337a0827'],
  '118618025'=>['size'=>6167721,'duration_ms'=>153652,'blob'=>'d7f6c81278bfdd43191fc288ef522ad6742b6ed4'],
  '45239761'=>['size'=>6770355,'duration_ms'=>167105,'blob'=>'e9bc1b014de3382658b55d7502a227300c10a996'],
  '45239757'=>['size'=>7957359,'duration_ms'=>196780,'blob'=>'b87ea9e6ccf04534c37ac384a3a7c1fe88d6529c'],
  '41249164'=>['size'=>8167363,'duration_ms'=>202005,'blob'=>'d44f1698a0d65e4f8d8d3816389389809aba88cf'],
  '48591480'=>['size'=>13049984,'duration_ms'=>324096,'blob'=>'d67a78883246a964ea3c57f3dca723968c1ed394'],
  '40498608'=>['size'=>4741561,'duration_ms'=>193933,'blob'=>'f2e7976b610f6aabc9e0202cc11ac92ca1fc2996'],
];
$pdo=null;
try{
    if(count($expected)!==200)throw new RuntimeException('wrong_plan_length');
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
    $verified=0;$absent=0;$catalogueAbsent=0;$bytes=0;$issues=[];$batch=[0,0,0,0];$ids=[];$ordinal=0;
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
    $pass=count($expected)===200 && $verified===200 && $absent===200
          && $batch===[50,50,50,50] && !$issues;
    $out=['status'=>'NEW200_BATCH1000_INDEPENDENT_READONLY','pass'=>$pass,'checked'=>200,
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
