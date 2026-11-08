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
  '115430106'=>['size'=>5280958,'duration_ms'=>131918,'blob'=>'4bb04c9952d9dad3a1f7c57f4437f63ca978ce05'],
  '142795082'=>['size'=>5128403,'duration_ms'=>128104,'blob'=>'ce095f4f318f0f4454a647b7a1aa68556516437b'],
  '148716122'=>['size'=>5558742,'duration_ms'=>137195,'blob'=>'18d6c4184119cd6d8f387f516ee69cef3c74f29a'],
  '104666232'=>['size'=>4658617,'duration_ms'=>114312,'blob'=>'969ddb94c2d3f56d732922e64dd44a64f89eb313'],
  '110689246'=>['size'=>4466356,'duration_ms'=>109505,'blob'=>'eaca01d37ababacc8fd04c3b3b375176239b445d'],
  '83371039'=>['size'=>6778715,'duration_ms'=>167314,'blob'=>'2ad0c76434033d1c7928ebf8efa30e28e9a37769'],
  '104666233'=>['size'=>4617866,'duration_ms'=>113293,'blob'=>'45877f25ac994d2c82f761ce3dd6a5d4c2b85f04'],
  '104397947'=>['size'=>5050454,'duration_ms'=>124108,'blob'=>'f54c779ff511300caed7cc27f099e3bd6cf749e8'],
  '104666237'=>['size'=>4887450,'duration_ms'=>120033,'blob'=>'98c283698ad9f5d518a8972f91755cf0d37b81a8'],
  '104666239'=>['size'=>4709817,'duration_ms'=>115592,'blob'=>'4b18236fd50822b4981dde2827faeb0115e42000'],
  '104508866'=>['size'=>4483074,'duration_ms'=>109923,'blob'=>'4bda852c45742c2c042bcb8ec11c173ae8e9f1c2'],
  '38931997'=>['size'=>3413704,'duration_ms'=>138606,'blob'=>'4f7a6cd5d937c5341cd4b8bd5ffb7d0a44073ffe'],
  '140701197'=>['size'=>4355179,'duration_ms'=>108774,'blob'=>'cb7d98fda417124183459998d913c9300e3a48e7'],
  '83215345'=>['size'=>5501474,'duration_ms'=>134165,'blob'=>'9494e31a6bbcb7580363c1a0dbaa11042b61f499'],
  '119923207'=>['size'=>6023358,'duration_ms'=>149838,'blob'=>'26dd05c95b34d5814f0836f2a89d3a52b92a5163'],
  '119923183'=>['size'=>5383881,'duration_ms'=>133851,'blob'=>'66c7f6c2e2d299bbe96e7634e65bae54170a5caa'],
  '96545843'=>['size'=>10938453,'duration_ms'=>271308,'blob'=>'ede48a1709292a0aeabf38abcd009be3728c0a85'],
  '131794590'=>['size'=>8903849,'duration_ms'=>220212,'blob'=>'f17b89d16d15d491ccf81df506e8278ffde3d8d1'],
  '131794588'=>['size'=>4644845,'duration_ms'=>113737,'blob'=>'a96328b48d94e22c8e73543d699a798df01ff2d8'],
  '138687506'=>['size'=>6401089,'duration_ms'=>159922,'blob'=>'46588e146c45d0396c082e40a60fed5e6add99a6'],
  '108726305'=>['size'=>5317948,'duration_ms'=>130795,'blob'=>'2aea25aa8c6a152d8e68832ab5436f14cf9f2648'],
  '59933954'=>['size'=>5667988,'duration_ms'=>139546,'blob'=>'094224ef252f884d102bd72a696dd434f4006451'],
  '108726303'=>['size'=>5653360,'duration_ms'=>139180,'blob'=>'db8e011c42595e1752d9d677232d8c9611402de0'],
  '108726304'=>['size'=>6411956,'duration_ms'=>158145,'blob'=>'a331fa98b2a4b98580c6e8d2ea0b8894c05a89ad'],
  '108726307'=>['size'=>5024331,'duration_ms'=>123455,'blob'=>'2dc43618be3637787fb2ce0d87b94d8c78bb83d3'],
  '117219711'=>['size'=>6524699,'duration_ms'=>160575,'blob'=>'72518199050503301172006cd54855f7afbd6285'],
  '108726306'=>['size'=>5284511,'duration_ms'=>129959,'blob'=>'07fa2a6624fbb7ae03c8cdbef374bd9ae0d648f2'],
  '48592481'=>['size'=>14368854,'duration_ms'=>357068,'blob'=>'b5f268161a71d7312d76a5bc00c18648f2cb6fa2'],
  '83832124'=>['size'=>5267793,'duration_ms'=>129541,'blob'=>'c195ca036a754eca4fe9f8641cda21a551ee89d0'],
  '142439257'=>['size'=>3402604,'duration_ms'=>212663,'blob'=>'4d4d96cf0e81790f87333976f3835875ade048f0'],
  '119296556'=>['size'=>5426617,'duration_ms'=>133512,'blob'=>'46978579050d17676dc086cf3a8c0328dd133388'],
  '125249908'=>['size'=>5873499,'duration_ms'=>145554,'blob'=>'8ac0a031925d457f9f1a1e56c017c4315fda5476'],
  '115902226'=>['size'=>7315228,'duration_ms'=>182596,'blob'=>'8b1816897c1cf6402d42a543decf6710c07001f4'],
  '62774310'=>['size'=>8436946,'duration_ms'=>208744,'blob'=>'c6ce349438d3495ea4af6c7156d27a8852b2c889'],
  '148716913'=>['size'=>7183596,'duration_ms'=>174054,'blob'=>'61005654381eeac211ba60f8ec61436e41b5d491'],
  '119296544'=>['size'=>5572903,'duration_ms'=>137169,'blob'=>'a5373cae8478c0765616f2e8b3fc392668c20366'],
  '118841484'=>['size'=>4606518,'duration_ms'=>114469,'blob'=>'3e565d49f53f4ee6f461812b3cc1da3dd99a3c9d'],
  '103247542'=>['size'=>8053470,'duration_ms'=>199158,'blob'=>'488f1df0452aab8a637d474d0e85464e5246c078'],
  '78745768'=>['size'=>4405602,'duration_ms'=>105665,'blob'=>'716bcc4f6416b465f1e71475cab4eef7d31b0175'],
  '121991178'=>['size'=>5195418,'duration_ms'=>129855,'blob'=>'53a6c5c14a4e15d0d2ef3cf49b12ea6ed04fee2d'],
  '77009786'=>['size'=>6547793,'duration_ms'=>161541,'blob'=>'3efcdf1b56bc0b4738696456a77b2267bc4c4ae3'],
  '114784200'=>['size'=>4082210,'duration_ms'=>101642,'blob'=>'8d97e9877b498e609f0754b99de3d1c2b0553f9c'],
  '99699705'=>['size'=>6962617,'duration_ms'=>171912,'blob'=>'12101cbfe98acf08ce21fda967455c510cd771ef'],
  '99699703'=>['size'=>4437099,'duration_ms'=>108774,'blob'=>'502325f88633dbac88aa57801833ec8ebcfdf887'],
  '83782742'=>['size'=>5012221,'duration_ms'=>121731,'blob'=>'13857fe963fa0064fc37b627c9c655762347e659'],
  '99699706'=>['size'=>4542633,'duration_ms'=>111412,'blob'=>'513b595eabf83c1363a985cf194c364ecc0b8fe8'],
  '114784204'=>['size'=>5128152,'duration_ms'=>127791,'blob'=>'af3f9c01e159586634c303df1038ae37dd582a4a'],
  '80159694'=>['size'=>4884294,'duration_ms'=>119928,'blob'=>'6ddd336a3914654be785ab6111df73f00cf3a4ca'],
  '107645946'=>['size'=>4275766,'duration_ms'=>106893,'blob'=>'c04f4ce3f523ee60a5fce61b5f4984e9360c903d'],
  '134188724'=>['size'=>3788844,'duration_ms'=>94616,'blob'=>'e5f8e9aa82157892110453a5de38fd94b081e1b3'],
  '148716119'=>['size'=>5420849,'duration_ms'=>135262,'blob'=>'f71c78ff30efcc4de012276709f0220fcb074f56'],
  '93556487'=>['size'=>6451662,'duration_ms'=>159138,'blob'=>'576455329ab3aaa424e148adca36d8be04ee6278'],
  '113990671'=>['size'=>5762656,'duration_ms'=>144065,'blob'=>'4120f6ba4fd27ada956e104896295349dc8eb114'],
  '93556497'=>['size'=>6145507,'duration_ms'=>151484,'blob'=>'cc68fba6dae3712d1e0b0f3c1b667b65b73161f6'],
  '36161916'=>['size'=>7056658,'duration_ms'=>174263,'blob'=>'32b3b7a25265dd45420084f0b359ffc7f3a7c0e7'],
  '66102259'=>['size'=>5036451,'duration_ms'=>206263,'blob'=>'548a61d867f01193821ba5ae7d2d99155d000843'],
  '141403817'=>['size'=>5736587,'duration_ms'=>138736,'blob'=>'acb3867e78b6dedb719551cd6b39eb284b9b0983'],
  '35758337'=>['size'=>7203570,'duration_ms'=>180088,'blob'=>'f4e172cf7ca7fc94b427e2342d21bf1652e6af84'],
  '108127245'=>['size'=>5783972,'duration_ms'=>142446,'blob'=>'d1f77fa487f85603ce79a8a83d165ddfd6f13430'],
  '85327084'=>['size'=>7042656,'duration_ms'=>176065,'blob'=>'eec9c06147dc1010d86ad8c6cab4b67b2106f3fb'],
  '117979417'=>['size'=>8413959,'duration_ms'=>208170,'blob'=>'d8af07a3d8b94ecc74a18dd5b3b593ac9ad5e9b0'],
  '88975675'=>['size'=>7255188,'duration_ms'=>179226,'blob'=>'a992d5c46ab0c5f4921d0e35a36bc0c38b90ba4d'],
  '75085736'=>['size'=>7863319,'duration_ms'=>194429,'blob'=>'4133309439b4db12a8f28d390a520abbd95dec0d'],
  '99923169'=>['size'=>5567544,'duration_ms'=>136202,'blob'=>'fb1f23a31396b06503a998fe100886e7497d0c79'],
  '38943639'=>['size'=>7247874,'duration_ms'=>179043,'blob'=>'8ab4b72046a399b0d3dbaf4b29461320d216b95c'],
  '106416103'=>['size'=>4711907,'duration_ms'=>115644,'blob'=>'c8694d24d5c49c534185402969ff61c3a991f28b'],
  '30087866'=>['size'=>6066074,'duration_ms'=>149473,'blob'=>'eb773b545d60fc1f1119eeaa52e22ad212451a57'],
  '114102000'=>['size'=>4415783,'duration_ms'=>110289,'blob'=>'653c725275196c086ad66a828b313ffea827881e'],
  '75541926'=>['size'=>6610363,'duration_ms'=>163579,'blob'=>'1ab231b9e0e4be9292d234d0262071441475d201'],
  '124711309'=>['size'=>5133481,'duration_ms'=>128052,'blob'=>'1d7d9a51a5a2e276006d83626a13b73225104867'],
  '111623625'=>['size'=>4005789,'duration_ms'=>91847,'blob'=>'9a05c388a97ae15ba53f1d636dbdd477f853ad06'],
  '136395876'=>['size'=>3951451,'duration_ms'=>98194,'blob'=>'6b9350f2b672a77c55f0b2ffe3e78524d676f63d'],
  '140712542'=>['size'=>3861652,'duration_ms'=>96026,'blob'=>'14aa4d452b3bc6f09846f137715d1d5a5b257acc'],
  '147212202'=>['size'=>6090126,'duration_ms'=>150100,'blob'=>'e1198c6a4e8a168f09a8923a9849675dc76c6be2'],
  '42938213'=>['size'=>12639130,'duration_ms'=>315873,'blob'=>'f04d72c283d4183d9f1d08d58ef9cb5b6373b81b'],
  '47684225'=>['size'=>8917621,'duration_ms'=>220787,'blob'=>'8727083f0cbcb21bcce7a8a39c0568900d00c91b'],
  '36161915'=>['size'=>5932348,'duration_ms'=>146155,'blob'=>'d0991719d687dc31bd4905f49183de6421c0b2da'],
  '108805148'=>['size'=>4708354,'duration_ms'=>117603,'blob'=>'8451ca45ef9ecc419b2ce2152f882dd0583fcdfb'],
  '147212206'=>['size'=>9432944,'duration_ms'=>231184,'blob'=>'e3054988b1e69a5301ace4b89d56ec6c03c46d0a'],
  '147651926'=>['size'=>9182935,'duration_ms'=>227605,'blob'=>'a2dbb9192001c5624f023fa71ae9cad7a522010c'],
  '110023299'=>['size'=>3305056,'duration_ms'=>82625,'blob'=>'338c14955e14834ef3bfdba06c7a82942c6b14ba'],
  '138562795'=>['size'=>3803243,'duration_ms'=>94694,'blob'=>'d704853536578300b8b1690dd8d21062f9e371bc'],
  '147212215'=>['size'=>11439054,'duration_ms'=>281287,'blob'=>'3c3e17e77532b53c9490fb31d6c10b9407b55ba8'],
  '147212200'=>['size'=>9436517,'duration_ms'=>235807,'blob'=>'790043bd22c0f461393bad273358e56aa7b57637'],
  '27317251'=>['size'=>7412946,'duration_ms'=>183144,'blob'=>'377201dc763159767467e295796ab1e6730659c5'],
  '105336877'=>['size'=>7715693,'duration_ms'=>186984,'blob'=>'7f73a5bf07c264acc935755e4676516b87e4a612'],
  '36142277'=>['size'=>4091237,'duration_ms'=>100127,'blob'=>'005749c7c844adbcc551b215f3ddfff9d30d8f91'],
  '126099536'=>['size'=>7400011,'duration_ms'=>184895,'blob'=>'7b26516ee4925ebc7168bd4572eaf82c15f34b7c'],
  '27317263'=>['size'=>8206142,'duration_ms'=>199784,'blob'=>'4c4ac338bdcf6c8b172079f4f8dc7c2710229998'],
  '138369290'=>['size'=>5762758,'duration_ms'=>142968,'blob'=>'d5d37e62d9011cdbd0d161e4ca21535acab6e4e4'],
  '141111607'=>['size'=>4266989,'duration_ms'=>104777,'blob'=>'dec0fba8ee0f41ee2e49ae5984b65571792553e3'],
  '36161931'=>['size'=>6993964,'duration_ms'=>172696,'blob'=>'78ddaa9282794f8588a1d41233b8dae472815bdb'],
  '148716094'=>['size'=>6317055,'duration_ms'=>156134,'blob'=>'2ef54ec1daf9e224b0352d659a448f46cb746d4f'],
  '130919973'=>['size'=>4225549,'duration_ms'=>105456,'blob'=>'b17e32d41e4835d94fcd9693539fe689c606f785'],
  '115063213'=>['size'=>5351928,'duration_ms'=>133590,'blob'=>'83ed46924384e1de13570b60b23ab5f293038f3a'],
  '45239755'=>['size'=>7048298,'duration_ms'=>174054,'blob'=>'3d99f0fc8d041e2dd6c85ff0e161471cd2e18334'],
  '129501469'=>['size'=>4947552,'duration_ms'=>123481,'blob'=>'36479d25407ee64bcfd4d9b5554d517bbfdd2353'],
  '113140429'=>['size'=>6962053,'duration_ms'=>173767,'blob'=>'8ca6bd665e8deab9bd1374626c85a201c41c8e34'],
  '40498602'=>['size'=>5123994,'duration_ms'=>209868,'blob'=>'1be0ca588ae68ed21b41bc99ab26e6fa1a9ac3d3'],
  '119359241'=>['size'=>7275334,'duration_ms'=>181368,'blob'=>'58c7c94e81340377c338b2ccb694c256b87fe422'],
  '104242339'=>['size'=>6028478,'duration_ms'=>148558,'blob'=>'ed387f8a52d60f350c7e392041eaec940b6c8767'],
  '108127248'=>['size'=>6371205,'duration_ms'=>157127,'blob'=>'6a0778433a4d30d4d039e0120cce56601839e477'],
  '108127266'=>['size'=>7175776,'duration_ms'=>177241,'blob'=>'6e49d64fcf62b7228ca00108e99ef466c321f083'],
  '36063275'=>['size'=>7884196,'duration_ms'=>194926,'blob'=>'561b4cdd6aaaff55009510570a82ff7c777526e8'],
  '34972339'=>['size'=>9079559,'duration_ms'=>224810,'blob'=>'ee5742abaee8330a9be1c9b9f5767cf20c6819e1'],
  '145536345'=>['size'=>5262777,'duration_ms'=>130952,'blob'=>'64e24ec228fa46c229e6a524a254a0d3c3be7920'],
  '145536339'=>['size'=>4791528,'duration_ms'=>119171,'blob'=>'2ff29daf768c94a2e41abee4b504add7851378a5'],
  '145536335'=>['size'=>5024540,'duration_ms'=>124996,'blob'=>'e07644d888c5cba09741644090c215f85f4e74da'],
  '145536337'=>['size'=>7163446,'duration_ms'=>178469,'blob'=>'74e447180ae605fe202ab5f1df3b127506e34a4f'],
  '145536342'=>['size'=>5097683,'duration_ms'=>126824,'blob'=>'61ec77b40435cf5b0ba4a9edfbcc2f6049c2890b'],
  '81936412'=>['size'=>6214658,'duration_ms'=>146913,'blob'=>'1b5da569c62e2930f4a7b1abeda21dec6fa5699f'],
  '77054879'=>['size'=>5959515,'duration_ms'=>146834,'blob'=>'f17cac35da5bfb89419b3592a6f59fafa2ed5990'],
  '145536334'=>['size'=>6285732,'duration_ms'=>156526,'blob'=>'7fc64688c25158b5ab1ed6a43f9b472ef99b0c80'],
  '106314854'=>['size'=>5393180,'duration_ms'=>132676,'blob'=>'e38401cded93caff960e0bc058e426eb7fa13505'],
  '116649703'=>['size'=>5831473,'duration_ms'=>145502,'blob'=>'392e0a5faea969c68677044bb7da69711ae82c03'],
  '119923197'=>['size'=>6335783,'duration_ms'=>157649,'blob'=>'1859e6243c95df02f6a3cc3db58f5fdbd3ff1a27'],
  '52765480'=>['size'=>6389991,'duration_ms'=>157571,'blob'=>'cadaf0980f83ff5d39f98dbf43f1ce8da2ebd137'],
  '138413376'=>['size'=>5090411,'duration_ms'=>126694,'blob'=>'7a3b58d44dfe5b446373a728f57f970dbd42fcd4'],
  '138413379'=>['size'=>3863700,'duration_ms'=>96026,'blob'=>'fc950b2d222904eb44ffa94d6fe4ef910928e8cb'],
  '132845882'=>['size'=>6462529,'duration_ms'=>161202,'blob'=>'5e09ccf62a4e1d9d8d8d07180845e89a851b4494'],
  '132845924'=>['size'=>6878398,'duration_ms'=>171598,'blob'=>'6572ec081843446285d3cbdc7321483dee231a97'],
  '90199334'=>['size'=>7739603,'duration_ms'=>193384,'blob'=>'c54047b367ac394788d8524dc99bbf65c7f72fa6'],
  '38931999'=>['size'=>6678383,'duration_ms'=>164780,'blob'=>'e8dc3d16b8a0630447d057fa3a364a17f94cf40e'],
  '138413380'=>['size'=>4432125,'duration_ms'=>110237,'blob'=>'b5502b6f1a678176938273d1211bff5d13ef6ef1'],
  '60051509'=>['size'=>6427629,'duration_ms'=>158537,'blob'=>'868bb4aa5c277aabbca3424210941f598433b513'],
  '117786990'=>['size'=>4989076,'duration_ms'=>124186,'blob'=>'2dd751008f39e25448673130c2e09430a33b7e5c'],
  '38932000'=>['size'=>7943754,'duration_ms'=>196415,'blob'=>'2d841c13cee2feef2fe20805fdd36dd30f0a629a'],
  '117786978'=>['size'=>5239852,'duration_ms'=>130456,'blob'=>'0fef75bad834e20b5fd7f56e192431006d64e04a'],
  '117786988'=>['size'=>6216832,'duration_ms'=>154880,'blob'=>'2a241ab735048641469f5254e14bb90402fca31f'],
  '117786986'=>['size'=>5303591,'duration_ms'=>132049,'blob'=>'d70e02d7a2104f31c7c3cb4b3f5a4d6891b0c9e1'],
  '117786975'=>['size'=>4751885,'duration_ms'=>118256,'blob'=>'ef10de293710bef5d2b1ac84e0f0b9b605a29c0e'],
  '117786973'=>['size'=>4889811,'duration_ms'=>121704,'blob'=>'715f90df7d9fb24ee46ed5157780d20cf9d0aba4'],
  '92607047'=>['size'=>5550960,'duration_ms'=>136620,'blob'=>'36c600a7f287c9af8a17f830e7213cd1cc3e7b35'],
  '138936959'=>['size'=>3994564,'duration_ms'=>99605,'blob'=>'049ed12137162179869ddf99794f9bedd904c347'],
  '123974149'=>['size'=>5132436,'duration_ms'=>128026,'blob'=>'a7f8698704ff897f9209a0da247aec9dd2504d87'],
  '119890671'=>['size'=>5133460,'duration_ms'=>128026,'blob'=>'66337b09f828dd0d6f14e0898dadf1060de0a133'],
  '109332245'=>['size'=>4927782,'duration_ms'=>123089,'blob'=>'6649a8849d6f4f8d5be3bc1308f7e42ab0ee7add'],
  '109332241'=>['size'=>5786061,'duration_ms'=>142498,'blob'=>'1e16c954eb0880cf6b07e755c4549771940056b9'],
  '109332246'=>['size'=>5176468,'duration_ms'=>129306,'blob'=>'d085d7b5ff297ed42047bac79b69817b47a324a4'],
  '111402811'=>['size'=>6161180,'duration_ms'=>151876,'blob'=>'b6afa351293b2a8ed80b634cfb06e5f6e60b972a'],
  '109332244'=>['size'=>7148190,'duration_ms'=>178599,'blob'=>'a4c4ee3b638ca7fe0cd1ff5c37915a28970c62ad'],
  '111402812'=>['size'=>6867531,'duration_ms'=>169535,'blob'=>'11b7390e60f7748c819f7b3fe81b74977728f28d'],
  '109332242'=>['size'=>5354518,'duration_ms'=>131709,'blob'=>'d55c3d12a87300b502f3aff756f3635add24c673'],
  '108021209'=>['size'=>5478862,'duration_ms'=>134818,'blob'=>'75194796d4658ecac878f6f8f48c1ac5afe2a3ea'],
  '111402810'=>['size'=>4275140,'duration_ms'=>104725,'blob'=>'9b1cd48b77702cf844ab7b1e76271fbd4d886c33'],
  '115308811'=>['size'=>5136532,'duration_ms'=>128026,'blob'=>'99c9b02d118bc35ee4d519c2ec1c8737f49756ac'],
  '103247531'=>['size'=>4722356,'duration_ms'=>115905,'blob'=>'02a79a5a6a9e5c332efcf190e5cecdcd31cf4052'],
  '109996948'=>['size'=>5128821,'duration_ms'=>126067,'blob'=>'0365801725c62afe38d5a9bacfa1794b1f89353b'],
  '112412060'=>['size'=>4729816,'duration_ms'=>117551,'blob'=>'0f6bbe0f899bc31d81a79c2b1afe116a018de555'],
  '48591466'=>['size'=>9861143,'duration_ms'=>244349,'blob'=>'15ad86d4d1edc677472de64e8de636a946e03506'],
  '112412062'=>['size'=>4386045,'duration_ms'=>108957,'blob'=>'965ecacdb0023cf9ea25ab9b960e975b5b8d440d'],
  '112412057'=>['size'=>5635743,'duration_ms'=>140199,'blob'=>'4a02ced1a5c0689495217893672f84c0c38009a0'],
  '112412052'=>['size'=>5789343,'duration_ms'=>144039,'blob'=>'65349ad387b60c1544ea24d1eafe27b010600ccf'],
  '112412059'=>['size'=>4829082,'duration_ms'=>120033,'blob'=>'cbbd1fb68fe307d017ba0f0812cccb165975dc4d'],
  '112412063'=>['size'=>4732951,'duration_ms'=>117629,'blob'=>'37d28e67c23be44fa8b4f2554048e417f33a7b2a'],
  '112412065'=>['size'=>6389114,'duration_ms'=>159033,'blob'=>'6c8aa700ed4cec6dc33100eacfdb711d1e8aecf2'],
  '73131630'=>['size'=>6255221,'duration_ms'=>154227,'blob'=>'9501614ec3184bc75522634f67686ed2e312e525'],
  '51998064'=>['size'=>7714842,'duration_ms'=>188787,'blob'=>'3a4d0a7f3a2c7a7b26a811f8aa21eb72e4b92066'],
  '17198411'=>['size'=>8807885,'duration_ms'=>218018,'blob'=>'37f630b795ab1093e05cb66d3b349974a2063634'],
  '119296549'=>['size'=>7077556,'duration_ms'=>174785,'blob'=>'a0b17ef8483e43315620a5f27ac46a8eb4d08e85'],
  '21220262'=>['size'=>8384702,'duration_ms'=>207438,'blob'=>'32a29dd8ba08850621e9daabf3b993595942168e'],
  '119359242'=>['size'=>6703775,'duration_ms'=>167079,'blob'=>'6efb37897bca539b46b631d9aae9bba083206292'],
  '130919971'=>['size'=>4378104,'duration_ms'=>109270,'blob'=>'9d519d68273aada281622ff8f5ab09cf47844e11'],
  '45239748'=>['size'=>5325261,'duration_ms'=>130978,'blob'=>'decdd5719cc682b06837b72756a1779c32b19ec7'],
  '112679396'=>['size'=>7122167,'duration_ms'=>176379,'blob'=>'07ad907b5a56fb7267460eec1f20c89c4a93ec56'],
  '112892660'=>['size'=>7485547,'duration_ms'=>186854,'blob'=>'38ff26ae903c4fe7433dc93e27583f96c5055366'],
  '130919918'=>['size'=>6026953,'duration_ms'=>150491,'blob'=>'12e8f9ff9a9bc334690ec69cc2913c69625f7f1e'],
  '61693507'=>['size'=>4818486,'duration_ms'=>118309,'blob'=>'d4d8542f4c7e774e12f833b088d58c7dac8b92b3'],
  '41249159'=>['size'=>8416048,'duration_ms'=>208222,'blob'=>'463f15e2688e7eee2acbc1c5f8cba4523a5f1355'],
  '83836709'=>['size'=>4887450,'duration_ms'=>120033,'blob'=>'8a7e5e64711552e17831996dec41296709b7dc90'],
  '131898071'=>['size'=>4483304,'duration_ms'=>108931,'blob'=>'243bcfed043db9ee304281c3f32e5cb38cb5a6d9'],
  '30087861'=>['size'=>6408245,'duration_ms'=>153078,'blob'=>'6cccca7768bd39544edcbdaf2bb65bf2a15a6fbe'],
  '27323562'=>['size'=>4268660,'duration_ms'=>266527,'blob'=>'75d84f80e49118da0f07998999527b4dec7427ae'],
  '104074051'=>['size'=>5408763,'duration_ms'=>130456,'blob'=>'7199826c23c05255c6750b915446757005d95397'],
  '119057930'=>['size'=>7500071,'duration_ms'=>187089,'blob'=>'dd608f65a76605109f8053c8b7df4eaae5caacd9'],
  '30087863'=>['size'=>9513192,'duration_ms'=>235651,'blob'=>'88e800e3e483ff9169cd5b71afd63c6b33ad69f0'],
  '30087864'=>['size'=>7431755,'duration_ms'=>183615,'blob'=>'cbd99bfb98512ab61805d64150500b8c6a38f10d'],
  '81936409'=>['size'=>4117360,'duration_ms'=>100780,'blob'=>'fb507d18e883b42ec2b5b0df63f3ec31fa2dea54'],
  '30087869'=>['size'=>6458955,'duration_ms'=>159295,'blob'=>'7b9b94c76f7a38cce91c01a830f2e7768593e052'],
  '93570866'=>['size'=>5795466,'duration_ms'=>142733,'blob'=>'0db2b9dbbb9f463dc235e0072c37f864546eccaa'],
  '148942881'=>['size'=>9708734,'duration_ms'=>230844,'blob'=>'6620199badb7588756a5b33c367d0dea618c8b61'],
  '93570865'=>['size'=>5625774,'duration_ms'=>140643,'blob'=>'5b1cc9486a498180a7ea1942563bf4c9b50b83d8'],
  '124752054'=>['size'=>3588224,'duration_ms'=>89600,'blob'=>'9eaa03fa1a3ef477eb8f8b5657bc08fbe185a0e6'],
  '30087867'=>['size'=>8394106,'duration_ms'=>207673,'blob'=>'3dd52a6b837423ee86f704a622b1ec6d1a2f2ee1'],
  '150988063'=>['size'=>7597497,'duration_ms'=>189832,'blob'=>'a54c6f907e1b4dee35c9f49e392709d796aec9eb'],
  '140085666'=>['size'=>6288196,'duration_ms'=>157205,'blob'=>'c62e6843b77a1b941bc28a3a116ff34d20583fb1'],
  '124181018'=>['size'=>4335326,'duration_ms'=>108278,'blob'=>'2996038a7c1b78e731bfd8e1faea28ca6638a6d4'],
  '108046214'=>['size'=>4456951,'duration_ms'=>109270,'blob'=>'ff8e89305f87bd329ab111dd177349fcf462950a'],
  '88273925'=>['size'=>3679548,'duration_ms'=>89835,'blob'=>'c214f4fc7e8d4ea167516c5a3daedcc651452b3b'],
  '89274168'=>['size'=>6195662,'duration_ms'=>152738,'blob'=>'b6c903fcb6b39fd59755ccd8c9a9c0c9c72626cc'],
  '125523428'=>['size'=>5377938,'duration_ms'=>130900,'blob'=>'1b1329daabc9b977b6e0929330cdb9a71e61e157'],
  '107819456'=>['size'=>8071254,'duration_ms'=>199628,'blob'=>'6aac5d4c6fbda272c000aeee89e5ea16674cfbaf'],
  '139748379'=>['size'=>5600841,'duration_ms'=>138971,'blob'=>'13ef74158967a2448155761979f3cd8dd485173f'],
  '106894276'=>['size'=>3696893,'duration_ms'=>92317,'blob'=>'13669e093b5d47eaa37c3f7c04983da0b13c5d79'],
  '137238387'=>['size'=>6486603,'duration_ms'=>161855,'blob'=>'35810f645dea1f9a777d18cb8cb2f19b58f7db28'],
  '106894277'=>['size'=>3655493,'duration_ms'=>89208,'blob'=>'2ad9d3ee38d9db8dec087434d9111aa3e3897054'],
  '106894279'=>['size'=>5368081,'duration_ms'=>132023,'blob'=>'679a1cdc3026e9f401d3f080d75f3e7bb5768a20'],
  '30087868'=>['size'=>7237404,'duration_ms'=>178756,'blob'=>'74ed964d73ec042e76dbdc24a4c62ecc7eb38ed3'],
  '106894278'=>['size'=>4204482,'duration_ms'=>100362,'blob'=>'9a48bc7cc279a015ff8f768d4e67852d1e6b45a2'],
  '106894280'=>['size'=>7057702,'duration_ms'=>174289,'blob'=>'6ae946c5a82b35b4bf0d2d0e0412fb3cefefde13'],
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
    $out=['status'=>'NEW200_BATCH400_INDEPENDENT_READONLY','pass'=>$pass,'checked'=>200,
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
