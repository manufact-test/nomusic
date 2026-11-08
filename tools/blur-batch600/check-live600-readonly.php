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
  '108756423'=>['size'=>6042689,'duration_ms'=>151066,'blob'=>'bf3e9b12985be392befdd8da0ed3194b43c7957c'],
  '125523427'=>['size'=>6241175,'duration_ms'=>156029,'blob'=>'481fdb308356080d4d67a695b97fa6ba4842b792'],
  '138899089'=>['size'=>5653942,'duration_ms'=>141349,'blob'=>'5a24dac4e9c0936668774f06276d94d4343ef59c'],
  '134260210'=>['size'=>4225567,'duration_ms'=>105639,'blob'=>'6be4deb3e9445b2697e5143552dc0d898bf37ef5'],
  '113095208'=>['size'=>3913178,'duration_ms'=>97176,'blob'=>'cfc7baa003cefd39d3cf474e03cd26948467b5c2'],
  '125967717'=>['size'=>5480489,'duration_ms'=>137012,'blob'=>'e943d8675c4c1690d04875a7bcde0c7921f5a637'],
  '45468214'=>['size'=>7205012,'duration_ms'=>177946,'blob'=>'0dbd6d7edbefada75b0e4a0476defc2687bc7681'],
  '111001120'=>['size'=>5223885,'duration_ms'=>128418,'blob'=>'022d8d35c4ef93bddeaec90de7509065711b8380'],
  '69046542'=>['size'=>6968104,'duration_ms'=>169874,'blob'=>'b169bd203cfa2a47da34cd819f6fbe73887b3556'],
  '70765563'=>['size'=>7357571,'duration_ms'=>183249,'blob'=>'9c6ff35ff012ff4188fe149cc1849068edcda648'],
  '79415117'=>['size'=>6104755,'duration_ms'=>150465,'blob'=>'33b149babeff3b4f2e7e707a6d2154bc71fb5508'],
  '111096030'=>['size'=>7029490,'duration_ms'=>173584,'blob'=>'4e5ea36ff32ab0f0afb4344f21056f98101e121e'],
  '131926723'=>['size'=>4921518,'duration_ms'=>120059,'blob'=>'fb1188ee97768acff2d916bf50823a824485be0b'],
  '98085667'=>['size'=>6293882,'duration_ms'=>155193,'blob'=>'61bb1cb15b1699ff1e4c56e6f40c86b92dcc59e7'],
  '118111188'=>['size'=>5502853,'duration_ms'=>136647,'blob'=>'5eb7defbbef98412c3a538b9c1d7ed7c5f647761'],
  '111001122'=>['size'=>3980477,'duration_ms'=>97358,'blob'=>'cd54fa15d60867d4ea8314b8506926a32555a4dc'],
  '116086498'=>['size'=>8706552,'duration_ms'=>216790,'blob'=>'539caa991eab8cc71e297a34f8507d2de84804e4'],
  '111001124'=>['size'=>5373326,'duration_ms'=>132180,'blob'=>'0cbc21f762e83372986884be873dc1af0066a35b'],
  '92193257'=>['size'=>4256331,'duration_ms'=>104255,'blob'=>'0fc4a60dc6ab3b471901881a7455c7033f41090d'],
  '122897352'=>['size'=>7745601,'duration_ms'=>193202,'blob'=>'ca3648e64a077c84de6e26149fe7a5a2eca8153e'],
  '114235473'=>['size'=>5523709,'duration_ms'=>137117,'blob'=>'fa2e4e2c1e5cdfbaf1ada3480ded12bd304d399b'],
  '128884518'=>['size'=>7824261,'duration_ms'=>184790,'blob'=>'96d72fc143b016f8736fc1f5abc44c1550577780'],
  '103889955'=>['size'=>7383710,'duration_ms'=>182439,'blob'=>'2796c19b846cc40ae2f936eef948e568c1a03809'],
  '114235480'=>['size'=>5268754,'duration_ms'=>130743,'blob'=>'23522b990b051fcf91b5d5847df6b34d7335f38d'],
  '108658411'=>['size'=>9226910,'duration_ms'=>228519,'blob'=>'a7ca9e744379eb564b6f7809114a7109e22b8f7c'],
  '123244387'=>['size'=>4870146,'duration_ms'=>121443,'blob'=>'8c86e2332341eccfb7ffcb9c6234027c08ad9739'],
  '119426246'=>['size'=>5629910,'duration_ms'=>140748,'blob'=>'93b0578b12ca7cce169024b4fa99ac6c5e6aa505'],
  '114116687'=>['size'=>3719525,'duration_ms'=>92447,'blob'=>'c6f6f60b1c4bb1afb31b92286bbc06ad68a6b12c'],
  '107622733'=>['size'=>2308064,'duration_ms'=>111096,'blob'=>'ffc17faaa571b092ca76842924885997a5f4fa14'],
  '109989523'=>['size'=>5337801,'duration_ms'=>131291,'blob'=>'1a020bbbfeb75292d2b54f2527ef7b926001d51a'],
  '107528942'=>['size'=>6774010,'duration_ms'=>168647,'blob'=>'0b00bab33242c083214ca15bd89e4157e59a69dd'],
  '105366595'=>['size'=>3989881,'duration_ms'=>97593,'blob'=>'b3ad4a232e4b845e1dd22a03b1e9614dda01d9bb'],
  '111124414'=>['size'=>3656064,'duration_ms'=>91296,'blob'=>'b1a2a2c4126c1667a43db2e4a0cc217be7797207'],
  '114984968'=>['size'=>3446784,'duration_ms'=>86064,'blob'=>'d77a291e4aff5f92794340f7acdc08e9b815ad14'],
  '109090867'=>['size'=>4911064,'duration_ms'=>122671,'blob'=>'45c5223cc80864ae4b42ead3e5e61e8a1288c536'],
  '95011123'=>['size'=>4990895,'duration_ms'=>122619,'blob'=>'ef17c38a4ebe95eda10ca1583626ab9d612ee5ba'],
  '120002920'=>['size'=>10267628,'duration_ms'=>254537,'blob'=>'361927bf5c89a5b83926071e918be29f4152bbee'],
  '112047067'=>['size'=>6449153,'duration_ms'=>161123,'blob'=>'9635bdef082e76121f310364511593257e4bf1aa'],
  '103704469'=>['size'=>8112587,'duration_ms'=>202815,'blob'=>'254b38686c96b1de158cbc8e08fca3d51b510ba2'],
  '107281308'=>['size'=>5609474,'duration_ms'=>138083,'blob'=>'880f7cdb6a6c87d96bffda8ab93722d513af6dd5'],
  '112047069'=>['size'=>5483668,'duration_ms'=>136986,'blob'=>'5dfa8e102982b9ae16f5d492cb0eea82b4e7421e'],
  '121793163'=>['size'=>7146285,'duration_ms'=>178656,'blob'=>'9478c870fc8b0a71adf4575cebac9ea8a6d2f2a2'],
  '128507522'=>['size'=>3973415,'duration_ms'=>98769,'blob'=>'93f03e0c91cfe55814f4e7f96393bfc02f7de861'],
  '128507523'=>['size'=>5679733,'duration_ms'=>141427,'blob'=>'cd3fe441cee63aa4f083eacd456851dfd14c0341'],
  '128507528'=>['size'=>3552321,'duration_ms'=>88242,'blob'=>'4fc7e96ad16b229ea30a1c4673e89c92ca2921eb'],
  '114101996'=>['size'=>3876615,'duration_ms'=>96810,'blob'=>'2dd7d4341778c5e24bd8418129c230ae24c0e0ed'],
  '128507529'=>['size'=>5214754,'duration_ms'=>129802,'blob'=>'88e3ef7e4f5c1a89e9429bc4f1f55c52b17f5a48'],
  '128237156'=>['size'=>5401277,'duration_ms'=>132519,'blob'=>'11df65125d23308018b0312e114ed692ec4a2b99'],
  '91779145'=>['size'=>7207122,'duration_ms'=>178024,'blob'=>'9de35d0bcbece59d1965dcdc00fd1185b8726ff7'],
  '93556500'=>['size'=>5486176,'duration_ms'=>135001,'blob'=>'dcc4cc37bbac590861f401f8b189594fc4e9a94d'],
  '148012030'=>['size'=>7737523,'duration_ms'=>169430,'blob'=>'00a3b405d661f7f2a08cb18ed5d8e081101d99cb'],
  '61843242'=>['size'=>7946890,'duration_ms'=>196493,'blob'=>'1621215e8082e4eb833283ae63897b1ff25fbf67'],
  '29508025'=>['size'=>6190437,'duration_ms'=>152607,'blob'=>'6278db75f2ff9e427377cee89dd03725381af333'],
  '48591728'=>['size'=>7934560,'duration_ms'=>326975,'blob'=>'e54189aa33dcd955852259d54008900923429f0e'],
  '29508027'=>['size'=>5652314,'duration_ms'=>139154,'blob'=>'ddfa7e8fc921b232a6a8714ddacb44a66a6acd8c'],
  '29508026'=>['size'=>5294960,'duration_ms'=>130220,'blob'=>'96990c43d368e5a75d764f7dd29b1d7e467a0def'],
  '130159416'=>['size'=>5491073,'duration_ms'=>135549,'blob'=>'b077e19a18fa8adf3b78f4f0e4f8fad15e67a7a5'],
  '29508044'=>['size'=>7575972,'duration_ms'=>187246,'blob'=>'478f441e8a05df3c8d7465746164c22cdab005bf'],
  '29508051'=>['size'=>6300152,'duration_ms'=>155350,'blob'=>'4bc41c0669b475a31abd49f55ae2902e42c4c292'],
  '109060764'=>['size'=>7689866,'duration_ms'=>190093,'blob'=>'c2ba83307d91c401bea9389c5e993602466012dd'],
  '29508052'=>['size'=>4383809,'duration_ms'=>107442,'blob'=>'046ed58873a7324642fe77a913962c7e73c94c0d'],
  '29508031'=>['size'=>8977180,'duration_ms'=>222276,'blob'=>'0888de8702e5a38814084354cabbd2fa98d392fa'],
  '29508034'=>['size'=>7191429,'duration_ms'=>177607,'blob'=>'68b086c430a1e558846830e4be0ba6ff6c7738f1'],
  '93556491'=>['size'=>4921931,'duration_ms'=>120895,'blob'=>'a859ed9ba26ae8fd7293ab7f71744ca74040e150'],
  '93556493'=>['size'=>5476772,'duration_ms'=>134766,'blob'=>'5a59bb34ac80cb23eb20a4970eff5cb0b5b1d4f2'],
  '138562790'=>['size'=>6417556,'duration_ms'=>160026,'blob'=>'a8c7efed15477dbb3224b98ab2e8fb321c5d06b9'],
  '93556496'=>['size'=>6999188,'duration_ms'=>172826,'blob'=>'de55e8a56dca8ff4b2c8a0b59a038b3b94484cb2'],
  '127365615'=>['size'=>6567855,'duration_ms'=>163579,'blob'=>'a4318ba6cff8c790806d194f309a13ff4239b861'],
  '93556495'=>['size'=>6636588,'duration_ms'=>163736,'blob'=>'db8c3c79a06f32412eab336e81207a52567c3b54'],
  '118841489'=>['size'=>6166551,'duration_ms'=>153469,'blob'=>'cdf73273c54040c41ff9c1522278fe22718302ab'],
  '133041138'=>['size'=>7066480,'duration_ms'=>176300,'blob'=>'7059b45f543c2d5cc29fd15efee9c2114da900ca'],
  '119359226'=>['size'=>6355824,'duration_ms'=>158380,'blob'=>'24eff9f9b3d0cb65b2674d3148dc1e6d8072cc23'],
  '45239759'=>['size'=>5277196,'duration_ms'=>129776,'blob'=>'d8f53b08f592bd66d6c6c9d012dc401291603e9f'],
  '48591488'=>['size'=>12569519,'duration_ms'=>312059,'blob'=>'863e05d7f4530038b2fcb88de63183279fd19149'],
  '106597497'=>['size'=>7306388,'duration_ms'=>180506,'blob'=>'96d05adb44d3408bcc0266066aeba5c19f0dd245'],
  '48591484'=>['size'=>13241388,'duration_ms'=>328856,'blob'=>'48607bd4bc5f585f9f6ad356c1a29d068aaa59fe'],
  '48591486'=>['size'=>10068033,'duration_ms'=>249522,'blob'=>'e3d20d984160cf2e20c2647cdfa91553cb7cb47e'],
  '40498604'=>['size'=>3579843,'duration_ms'=>145528,'blob'=>'b0befcc77f0a5bc11700fb6f52f2fc16ea0e43f8'],
  '40498607'=>['size'=>3783599,'duration_ms'=>154018,'blob'=>'d1eebac1f5857851b3f19f68cab7a4f77df94c52'],
  '131121688'=>['size'=>4788435,'duration_ms'=>119144,'blob'=>'c6af33185abda57d77e6af88316e657f0bbb6791'],
  '83836678'=>['size'=>5012837,'duration_ms'=>123167,'blob'=>'a1e8f6f2af5c869241729f00433f507bc2cec1fd'],
  '45239765'=>['size'=>5706649,'duration_ms'=>140513,'blob'=>'52a05f748ef198b694cf07c808c1f9d95efde66c'],
  '109060770'=>['size'=>5680527,'duration_ms'=>139860,'blob'=>'50de3f8a1b79404a9592e9414fa774f20c46677a'],
  '131898073'=>['size'=>5136365,'duration_ms'=>125257,'blob'=>'c3c0121ea7632bdad7f66fc76844d470f014f79a'],
  '42237527'=>['size'=>6864376,'duration_ms'=>169430,'blob'=>'89394d52ae7adce84f385b729a9f4b4077b634e8'],
  '141335101'=>['size'=>4830106,'duration_ms'=>120033,'blob'=>'ba11c20abf31f22310cc80625a709a74fc462056'],
  '135264160'=>['size'=>4186762,'duration_ms'=>104333,'blob'=>'4742ee52c15013876e81e66e9b33a4fbf0634084'],
  '34972348'=>['size'=>14015657,'duration_ms'=>348212,'blob'=>'3b9093429c6daa28a4486ec90c303860b5ed1da5'],
  '104429148'=>['size'=>7462562,'duration_ms'=>180062,'blob'=>'eba278a3e96b952e394fbfd3d183b36e432f6644'],
  '116728295'=>['size'=>6244040,'duration_ms'=>154880,'blob'=>'cf4c66bfa0dd8d4b1c0f683127a064e7e4aad911'],
  '110263046'=>['size'=>5922943,'duration_ms'=>145920,'blob'=>'60f07e9a1a7412101fd4ed06f37fbd06b6cf7649'],
  '137321624'=>['size'=>4581877,'duration_ms'=>114547,'blob'=>'4960e8a8f25d5f134aed653a363eac31f1391763'],
  '146196962'=>['size'=>5064045,'duration_ms'=>126600,'blob'=>'9643d60137e7f9010437673512590d962d0129c5'],
  '124415056'=>['size'=>9311130,'duration_ms'=>232673,'blob'=>'794b7197b60ca7cdf0b2842c29bed15438b926ea'],
  '69420955'=>['size'=>5127776,'duration_ms'=>126041,'blob'=>'ca4ea3ee5a76473723360e332474ed12a4fcb775'],
  '136272298'=>['size'=>6747792,'duration_ms'=>168046,'blob'=>'3db0bb111302b84ee45b377abdefa7c6cc8c542f'],
  '124732867'=>['size'=>6729584,'duration_ms'=>167340,'blob'=>'d8bb34dd74a535ab3ad83ff7c29087357e0a140e'],
  '139046043'=>['size'=>7234917,'duration_ms'=>180872,'blob'=>'9057250b8706397bf687772288753e3ce1a63e55'],
  '132182987'=>['size'=>6039937,'duration_ms'=>150622,'blob'=>'af0e881facab1736f8b27127fa31800ac40ec2ab'],
  '131971598'=>['size'=>3891934,'duration_ms'=>96758,'blob'=>'2fd79a09eb7577b1278b18d87eb30b845ba346d6'],
  '21287099'=>['size'=>7037829,'duration_ms'=>173767,'blob'=>'f5d2adf00af9e2083df7277bdb03cdd5bba706b5'],
  '117095821'=>['size'=>5656641,'duration_ms'=>140722,'blob'=>'ed0aa2532d45b267ea2440c04c4fe3808b4f3d59'],
  '143243394'=>['size'=>5472175,'duration_ms'=>136699,'blob'=>'8d481539cba2b186a977a28c7dc8586c199331aa'],
  '106619075'=>['size'=>7644583,'duration_ms'=>190224,'blob'=>'6035e706e47d491b65cec090e86454f0424fb51e'],
  '53582338'=>['size'=>12144265,'duration_ms'=>301453,'blob'=>'8c9a9a0cdb89ecf8ef0b9cd4ae1c2bfc411c5fa3'],
  '79980729'=>['size'=>6897812,'duration_ms'=>170266,'blob'=>'4a2766a52104087036a73207a852a9aa1a91acf6'],
  '47354657'=>['size'=>8201866,'duration_ms'=>202893,'blob'=>'98370a0c6497c6a8347416966e89ba7b0c3a7839'],
  '57185716'=>['size'=>6998770,'duration_ms'=>174968,'blob'=>'c75003f3ecaf55e2d6ff537db8594f3d57740c7b'],
  '113384828'=>['size'=>4038863,'duration_ms'=>99762,'blob'=>'c1d5aedd55f570d7c11e032398e87d1a48d8dd7d'],
  '80849470'=>['size'=>3948544,'duration_ms'=>98691,'blob'=>'de00ca89f212fe375ed305e5385b196064a03e66'],
  '148716123'=>['size'=>6258857,'duration_ms'=>156212,'blob'=>'c036bde0192216c4d4e232d8414622152b33642a'],
  '148715952'=>['size'=>6036837,'duration_ms'=>148767,'blob'=>'35fe1ee7c3d55036c1ba47e6b4359453aa5e47cc'],
  '105007663'=>['size'=>5343025,'duration_ms'=>131422,'blob'=>'42ce0caccc222e220721306a9b0969436ce91307'],
  '45551598'=>['size'=>9823526,'duration_ms'=>243409,'blob'=>'9693879ad2999cd66ae9a3336b28d5cb806ab66a'],
  '107329119'=>['size'=>7457955,'duration_ms'=>184660,'blob'=>'1c90fe9d6d08f3b43a124f4d9f9ad11d78d9f80c'],
  '141826350'=>['size'=>3349987,'duration_ms'=>83644,'blob'=>'5344c14902884e4e660bd738fa288881365744de'],
  '125535666'=>['size'=>5745388,'duration_ms'=>141479,'blob'=>'a05fc46a125c32636b26770dec4ac5c80524e7eb'],
  '79405420'=>['size'=>7552984,'duration_ms'=>186671,'blob'=>'831d6cbbbf7f5fa7ccd181923d1b0949e183885a'],
  '60161136'=>['size'=>5676347,'duration_ms'=>139755,'blob'=>'e7676025281787834ae6ddd5dc5298bf64d7f3b8'],
  '137826264'=>['size'=>6270309,'duration_ms'=>156447,'blob'=>'0e415dfb0f50117cd64c005908a0f1e11abe5291'],
  '113990669'=>['size'=>4684238,'duration_ms'=>116898,'blob'=>'fb374085a1a4b258d7446403403d77a05de4e6e9'],
  '105382846'=>['size'=>9064931,'duration_ms'=>224444,'blob'=>'78cd83cf0ca7fe377a11e94d0469b20a635b1639'],
  '119520466'=>['size'=>6399814,'duration_ms'=>159608,'blob'=>'cfdf251073ed237d4aa24a8c28d4d6ef4f79c498'],
  '139952380'=>['size'=>3876615,'duration_ms'=>96810,'blob'=>'ef8c4db496073a4a6577b575949d6efe3aad4a61'],
  '40254858'=>['size'=>6579118,'duration_ms'=>270498,'blob'=>'458ccf561fb960593e85d5eaddd12060bac49773'],
  '36342200'=>['size'=>6194177,'duration_ms'=>254459,'blob'=>'202b62aa874550f8c4187aa74d02ef8fb1ceb378'],
  '148715974'=>['size'=>8412935,'duration_ms'=>208170,'blob'=>'b984ec7c7f685c119518241499c2bd548cb544bf'],
  '138854073'=>['size'=>3941956,'duration_ms'=>96653,'blob'=>'553444b89ff363c7e2e8e4724db2d8fbc90a1b78'],
  '104798552'=>['size'=>5574993,'duration_ms'=>137221,'blob'=>'19985abff9977a7f04a3709527fd790913b658e1'],
  '105101211'=>['size'=>5185246,'duration_ms'=>127478,'blob'=>'03b9c399672d20b4c0a333e5c842121ec9f5d2db'],
  '127453752'=>['size'=>5430685,'duration_ms'=>133851,'blob'=>'018070108b786265a8431d1d6f1ebcf2a425dcb0'],
  '149231994'=>['size'=>1975318,'duration_ms'=>123455,'blob'=>'e0199ea92d69b06f0d113001f5c5410b9bf5c130'],
  '121793175'=>['size'=>4653393,'duration_ms'=>115461,'blob'=>'88a0fae6f7a8579c567e8c119fe9fe2a795dfe50'],
  '130989227'=>['size'=>4644615,'duration_ms'=>116010,'blob'=>'34c6b6ceb2c5428abb6d057913ceb15f727ca4c8'],
  '133174455'=>['size'=>4540564,'duration_ms'=>108826,'blob'=>'17ea96225b7a83011eeeed6b1ec815e35a6bcc1f'],
  '93012513'=>['size'=>2927848,'duration_ms'=>73091,'blob'=>'349e17ba1d91e73b2266fd2c107389b6739ba625'],
  '113384831'=>['size'=>3894673,'duration_ms'=>96157,'blob'=>'abbab086a0535dfb1f7d41aaae1a711669377df6'],
  '80159692'=>['size'=>5848735,'duration_ms'=>144039,'blob'=>'94bc830010a45378a02496d353b447249d30cba1'],
  '123214892'=>['size'=>5056305,'duration_ms'=>126302,'blob'=>'e8476511a16f552d41ad634b409cd51cf4f09824'],
  '147212194'=>['size'=>7562415,'duration_ms'=>181995,'blob'=>'e7758c150363d4b4bfe23b373b0f5b501b4cbcf4'],
  '119946332'=>['size'=>3920457,'duration_ms'=>98011,'blob'=>'de1be4451b97c129667ed26753db56e7f58c1776'],
  '123214893'=>['size'=>6747995,'duration_ms'=>168594,'blob'=>'c5929a1eb6adc6f642a626bfd698d2d7f9da71aa'],
  '36161919'=>['size'=>7556119,'duration_ms'=>186749,'blob'=>'bc18a8f5c7c95adb0fda37771dc991f4aa52aa5f'],
  '95699206'=>['size'=>3133066,'duration_ms'=>76173,'blob'=>'d3d31060b8d055c90dac133b45051429c645665a'],
  '128027859'=>['size'=>5008657,'duration_ms'=>123063,'blob'=>'26f8b56e92c4f24cf7ba0b03b6e89c3e4e506dca'],
  '132559741'=>['size'=>8037399,'duration_ms'=>200829,'blob'=>'8f71d1dd6a50acf49fb4f64ea6e4971c114ff3c7'],
  '136395879'=>['size'=>5968104,'duration_ms'=>148611,'blob'=>'b580b9599e49bd0733f08962f17764833bca5c3a'],
  '148716988'=>['size'=>5135090,'duration_ms'=>126224,'blob'=>'9b0911d25981ac74bb6c27df92524701c94d840e'],
  '74257868'=>['size'=>8398848,'duration_ms'=>262400,'blob'=>'3e27dea85252699d510defcabde2634e70040b56'],
  '76711317'=>['size'=>7218617,'duration_ms'=>178312,'blob'=>'6439fb2cb0a68ab6ae65d065247fcaae3fc0df6b'],
  '48596152'=>['size'=>7709432,'duration_ms'=>190746,'blob'=>'679b1d5c98ef36943ec9dee8ac3c7f9e2f37384e'],
  '109051372'=>['size'=>3268902,'duration_ms'=>79569,'blob'=>'af73dfc7d3da8298bafafac1b7a7c70fbb7526e2'],
  '92607043'=>['size'=>4738029,'duration_ms'=>116297,'blob'=>'fd0a803ff88af446d8ad31cd3e5bfa15fb429617'],
  '109051374'=>['size'=>5054632,'duration_ms'=>124212,'blob'=>'b14f5d3505c9bf7d7ca8fa655bbc8878de0561fc'],
  '109051371'=>['size'=>4826845,'duration_ms'=>118518,'blob'=>'35e1a799fa83cef93dbe74c6a3d142890aa27150'],
  '58810153'=>['size'=>6551971,'duration_ms'=>161646,'blob'=>'b6bb59973aa4f03a5b7914be2e84ddaf79e0f98b'],
  '109051373'=>['size'=>5848755,'duration_ms'=>144065,'blob'=>'0ecfc5c1ab02095a8f5686f8e927fef2069abf2f'],
  '109051376'=>['size'=>4415155,'duration_ms'=>108225,'blob'=>'405bc09a3a3c53fec41daf96625bcea24224e69a'],
  '109051379'=>['size'=>7822567,'duration_ms'=>193411,'blob'=>'24f1a939324d7e96f804abd615c1a1e422523514'],
  '46951717'=>['size'=>12285305,'duration_ms'=>304953,'blob'=>'6f6cbad8c32171ac9c00cdb405f528d722bc7fd7'],
  '109051377'=>['size'=>7217550,'duration_ms'=>178260,'blob'=>'fdef64e340c77dd8d9e0953f3223a4bcbb1d561c'],
  '109051378'=>['size'=>4301261,'duration_ms'=>105378,'blob'=>'8645a312f22aee701081f9465ad802cee4d1e678'],
  '109051382'=>['size'=>5114192,'duration_ms'=>125701,'blob'=>'d35c4c5f5c94be5b0a26c569326663eb802267c7'],
  '109051386'=>['size'=>4813261,'duration_ms'=>118178,'blob'=>'eb1c3453dc7035cbc4f2a17906ff47d326e3c806'],
  '109051384'=>['size'=>7357588,'duration_ms'=>181786,'blob'=>'4fe18bafff4b2c6510076845d96c9d6d417f79dc'],
  '109051380'=>['size'=>7325196,'duration_ms'=>180976,'blob'=>'d5a5d9385afe19579bb00d9af3da215ad535b821'],
  '109051385'=>['size'=>9094187,'duration_ms'=>225176,'blob'=>'4381128a770c8c21795b6a94c3c9138c1c63ae42'],
  '137804024'=>['size'=>3747048,'duration_ms'=>93571,'blob'=>'6c78779a18585ba17b5e2f6eb179681932aab569'],
  '53685466'=>['size'=>7300746,'duration_ms'=>182413,'blob'=>'be6fdf59a6723a74e3d9f72289da901f266d7d02'],
  '129925713'=>['size'=>4823293,'duration_ms'=>120581,'blob'=>'ac0c2bb4209a3437bd7a7d4d73a89842dedd35b2'],
  '137656529'=>['size'=>3090413,'duration_ms'=>127269,'blob'=>'9740ee007e4c1ebf694622dfa845e6ec84bec49b'],
  '81292490'=>['size'=>6554062,'duration_ms'=>161698,'blob'=>'3965d11ef9cfb55842f1518e8c23b26e6874fff3'],
  '62792247'=>['size'=>4739680,'duration_ms'=>193855,'blob'=>'ce984bbf5429ea44b6ffe23c7401d25c83a92374'],
  '48591459'=>['size'=>8692947,'duration_ms'=>215144,'blob'=>'184e78cb7756d18441c1c8f5cbcb1f2e02752f3b'],
  '48919489'=>['size'=>6488212,'duration_ms'=>160026,'blob'=>'121ee4d4963ca4b24762e150eaf5e23757d567d1'],
  '117680717'=>['size'=>4447129,'duration_ms'=>111073,'blob'=>'15cf0900af2216498fb1739ae882d57cad42a61f'],
  '136026615'=>['size'=>4520985,'duration_ms'=>109923,'blob'=>'dc405b2ab1cbdc15d50d583636e1e8c3568adf68'],
  '130169686'=>['size'=>6501355,'duration_ms'=>162534,'blob'=>'8ed744faa0c67ed9fbcbbabe18d5b0d76de4a928'],
  '117929984'=>['size'=>7068361,'duration_ms'=>176091,'blob'=>'1115562a194a7ed7346b0ccf4ecfcda87527769a'],
  '60058836'=>['size'=>6600037,'duration_ms'=>162847,'blob'=>'cb0d5ca989f80e4d462b31b6dfcc61f073d68b72'],
  '77009791'=>['size'=>5937572,'duration_ms'=>146286,'blob'=>'3f69360b22b0533edeeeec5a79cdf02881c93320'],
  '48591464'=>['size'=>7422998,'duration_ms'=>185469,'blob'=>'325e41cbcf2c2adce972b342a8ccf5e180f94cf0'],
  '90842069'=>['size'=>8007515,'duration_ms'=>198034,'blob'=>'c43ce3bc764b414340fbc84749df36da9abb4fc4'],
  '113680839'=>['size'=>6112154,'duration_ms'=>152033,'blob'=>'e86aa39fe2cc1a4fe8e183659a0da636a482f3d4'],
  '45239747'=>['size'=>4610565,'duration_ms'=>189336,'blob'=>'4518b7285ba99abde0d774b4e36827486bceb88f'],
  '81936407'=>['size'=>4935515,'duration_ms'=>121234,'blob'=>'c79d7ebca3b4e5c3b61ec90669cb0160c45ed732'],
  '66938935'=>['size'=>3136201,'duration_ms'=>127086,'blob'=>'0d6a3b270a435a5b808818ad993a3f516288c9c6'],
  '66668864'=>['size'=>4562486,'duration_ms'=>186514,'blob'=>'8125258f2fcd9160c60c959c5d0e59005c350ef4'],
  '93556494'=>['size'=>5666923,'duration_ms'=>139494,'blob'=>'c2d190c40e7cff783d814964c275545ce3c5c479'],
  '73495731'=>['size'=>6046242,'duration_ms'=>149002,'blob'=>'cd64ec66eafbe9c83348538e096bc6bde96c1707'],
  '40498612'=>['size'=>5107066,'duration_ms'=>209162,'blob'=>'97a6924a5e9f4e6aed5e423c45323af979f26eb7'],
  '151431532'=>['size'=>7986617,'duration_ms'=>197512,'blob'=>'05affe3ba9349a015ecc9be51de2170869459028'],
  '64015290'=>['size'=>7984526,'duration_ms'=>197460,'blob'=>'8ca1a175230757addad847391b7b82c857e22048'],
  '149219587'=>['size'=>7454346,'duration_ms'=>186253,'blob'=>'261aad11072e1177d3e6cfe35875bab96de7b488'],
  '106574623'=>['size'=>4169604,'duration_ms'=>102087,'blob'=>'9e4a1194ab72684bd16b7dcf38c131084f0ce1ed'],
  '43504917'=>['size'=>8090040,'duration_ms'=>200072,'blob'=>'b21114cf271ed67c773c3ba0165706873b6efe2a'],
  '149171834'=>['size'=>6604217,'duration_ms'=>162952,'blob'=>'5638e114a067e11ebfa76a824110bdf2f32cef5d'],
  '43532695'=>['size'=>7372217,'duration_ms'=>182152,'blob'=>'f0e8806dc133bb108b13dc031fa260fff9d150a4'],
  '72582098'=>['size'=>7192474,'duration_ms'=>177633,'blob'=>'7ff27c72cb9c88962d280d58166a1274ca9528d7'],
  '76788657'=>['size'=>5857115,'duration_ms'=>144274,'blob'=>'f05957a55cc94e62fab201a4e9733a44c7485499'],
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
    $out=['status'=>'NEW200_BATCH600_INDEPENDENT_READONLY','pass'=>$pass,'checked'=>200,
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
