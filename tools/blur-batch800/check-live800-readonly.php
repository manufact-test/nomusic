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
  '107544285'=>['size'=>4887450,'duration_ms'=>120033,'blob'=>'5cfe8e9ed492f67ad3fef9e35a65a544d2716d97'],
  '134997178'=>['size'=>6159947,'duration_ms'=>152895,'blob'=>'c769e5aa689dfe9e59d424434b0351d0c5aaa65b'],
  '115682364'=>['size'=>3779716,'duration_ms'=>93780,'blob'=>'277d1fab5e8b2091e6998884992c3bb3f4cf4b44'],
  '128831134'=>['size'=>5673796,'duration_ms'=>141845,'blob'=>'b644445bb7d3a39ec43d751d769b41a9c801ef03'],
  '133174442'=>['size'=>5891618,'duration_ms'=>142602,'blob'=>'3a4d1bf1bc0ee3e37946e6359e950b5efc486ae1'],
  '117505549'=>['size'=>7043910,'duration_ms'=>174968,'blob'=>'873fadf16776c9b53b1b6659b0de41bafcc55819'],
  '112679395'=>['size'=>6444974,'duration_ms'=>161019,'blob'=>'c9c2244ac462568bf30b47d8683e0bb1a4e98ee8'],
  '119280175'=>['size'=>7176633,'duration_ms'=>178312,'blob'=>'54d1ee1f7daec48a4d46c8a241396d7eeefec592'],
  '38690302'=>['size'=>7068131,'duration_ms'=>174524,'blob'=>'8f8cd78b2870d08ccd60304b61f5d91bc9e6430d'],
  '85095956'=>['size'=>5201964,'duration_ms'=>127896,'blob'=>'57c9158f3c986afef2452f8af278181fd8f389d8'],
  '41900827'=>['size'=>8488751,'duration_ms'=>212219,'blob'=>'aec106c9059f67544b5d7aed309b8d6e84928c08'],
  '119296540'=>['size'=>5548220,'duration_ms'=>137169,'blob'=>'7f249a37590f9f9a71fcf0dc46da682e4f8cfbc8'],
  '108393736'=>['size'=>5677371,'duration_ms'=>139755,'blob'=>'1c07b1b699450106182aabf7fd834c1c55a994ef'],
  '103574254'=>['size'=>4423338,'duration_ms'=>108069,'blob'=>'d644294be0a56f4a3ec27fb160dc6e1ab41f9fb5'],
  '149146246'=>['size'=>8421295,'duration_ms'=>208379,'blob'=>'a598bbaccaa02ebfe11eab3520b434291cb4c1c4'],
  '61221107'=>['size'=>4833115,'duration_ms'=>118674,'blob'=>'bb2b7cee4ac799623863b8f2d999eac37f6718a3'],
  '58810157'=>['size'=>3320750,'duration_ms'=>138188,'blob'=>'a3dbb17bc71d3a74814bbd60dbc73839bd44dee1'],
  '137497429'=>['size'=>4427277,'duration_ms'=>110576,'blob'=>'d6869fe72cadcc0f65eb20e7fad530066f3b978d'],
  '81936401'=>['size'=>4277544,'duration_ms'=>98534,'blob'=>'80c5fcbdefb5018429a8a61e4c0fe84b6338f76a'],
  '136598162'=>['size'=>4739701,'duration_ms'=>118387,'blob'=>'c825b49d2cc7c3bee028d6110977d8a67cabd424'],
  '116515484'=>['size'=>8394085,'duration_ms'=>208927,'blob'=>'29e0dc9f8b4a0d13b0a978f73b0936ee497b7dd6'],
  '116649708'=>['size'=>5672649,'duration_ms'=>141531,'blob'=>'81c16f19ebbcc42cf376b8cdc090076f5ead5cdf'],
  '133174435'=>['size'=>5874821,'duration_ms'=>139233,'blob'=>'b90f060a1878117aab89d7fa3bedd90cb448b61a'],
  '119296515'=>['size'=>5975192,'duration_ms'=>147174,'blob'=>'d539c6e42fda0ff81bdda383c696244b7195510c'],
  '121385451'=>['size'=>4321698,'duration_ms'=>108042,'blob'=>'9a2d6f17e3daf155b496df3872e936e10d95fa42'],
  '53223217'=>['size'=>8538048,'duration_ms'=>211272,'blob'=>'1d752b2059d4fbe8ca5fb658f1a930bccaf79890'],
  '112220712'=>['size'=>5062958,'duration_ms'=>113737,'blob'=>'ed79da5935a2df0932babd6de0a45e6bb6ad0428'],
  '99697481'=>['size'=>4376494,'duration_ms'=>107259,'blob'=>'1f2d40ccdf455bad8d98eab3c5331289ccb312c0'],
  '81936417'=>['size'=>9738890,'duration_ms'=>241293,'blob'=>'7a722bd3d0fc327d63159a278ad46c10fc9ba685'],
  '49336734'=>['size'=>8611968,'duration_ms'=>215249,'blob'=>'3bc67cad84a2a0883d273b87680149f510bd7233'],
  '127212428'=>['size'=>6764066,'duration_ms'=>168202,'blob'=>'1b620b4b728586881c08e54c32bdbf2d2d2544d1'],
  '103303171'=>['size'=>6343620,'duration_ms'=>158485,'blob'=>'27ccb3833f7fb738ba90798ed00dcb930c19dce3'],
  '106067863'=>['size'=>5960565,'duration_ms'=>147226,'blob'=>'5f27c92421a23d6608072a53e3d1ecda4a7dc9de'],
  '43504918'=>['size'=>12375188,'duration_ms'=>307226,'blob'=>'8a91fbfaf392a15778d17fe8a9be737b16262adc'],
  '109990504'=>['size'=>7034714,'duration_ms'=>173714,'blob'=>'7a9b1c1d895407c2bad9634a4e685970b3409439'],
  '53256122'=>['size'=>6595440,'duration_ms'=>164885,'blob'=>'ac70e8dd4446482fb21485b7b1eef64f43dc9449'],
  '110023310'=>['size'=>4564158,'duration_ms'=>113998,'blob'=>'038f45093b04bb29b45c9de8bc667ff5d9b8385f'],
  '73375329'=>['size'=>6700327,'duration_ms'=>165329,'blob'=>'a38f4f8ad2b9fa21b4587d1b88cb3c65728e1073'],
  '148716977'=>['size'=>6061453,'duration_ms'=>151536,'blob'=>'d40f11f52050e73e251245e9301372271bd01b42'],
  '85971535'=>['size'=>5149719,'duration_ms'=>126589,'blob'=>'3044cde3da527d93c42a936afa5e9647634b6c35'],
  '131898080'=>['size'=>4980676,'duration_ms'=>121365,'blob'=>'4fe5fb802b92ddc4871fa54ef52d051564d3b87d'],
  '72737512'=>['size'=>4731760,'duration_ms'=>116140,'blob'=>'0f93063d214f8552162ec94d94a837b4bcc7d379'],
  '144935313'=>['size'=>4613268,'duration_ms'=>115226,'blob'=>'266005a74fff8b51f9a4ea4a48aacc093a6e9e7d'],
  '89104835'=>['size'=>8442366,'duration_ms'=>208901,'blob'=>'8e98ed7590cf2719a2eebed04526a24bf90dbb53'],
  '110023312'=>['size'=>4214073,'duration_ms'=>105352,'blob'=>'15742bc0d42c9a387c90e43a40b2f3b63f12a9c9'],
  '82790447'=>['size'=>3186606,'duration_ms'=>131553,'blob'=>'9e9b41d09913436c9ac5446d65f1f33310a940da'],
  '51950492'=>['size'=>7208168,'duration_ms'=>178051,'blob'=>'fcd27b6f4ba858d194467b251931405d5a3a41b4'],
  '148715962'=>['size'=>6971559,'duration_ms'=>174289,'blob'=>'5ba6b8886fa2456db32df42fe7ffb9b2388c64aa'],
  '128507538'=>['size'=>4421676,'duration_ms'=>109976,'blob'=>'76e5412b6acdcbe559aacbdaa6439328e636443b'],
  '133706042'=>['size'=>5595428,'duration_ms'=>139886,'blob'=>'389293dc38a9ae41a01003f0dc871eeb7c7be6c8'],
  '109110867'=>['size'=>7481469,'duration_ms'=>187037,'blob'=>'3d7181ef117ac9666446adeaa104187f9f9013b7'],
  '119728718'=>['size'=>7202525,'duration_ms'=>180062,'blob'=>'8e88cfdfc15a19346c1df99b716436515d1bb488'],
  '48928606'=>['size'=>5335134,'duration_ms'=>222119,'blob'=>'b923c4ed56c7a39cb5c255214da74d73776cf5c1'],
  '104817646'=>['size'=>5711821,'duration_ms'=>142315,'blob'=>'ed215ce90e0fbc6c0363cea7d10c9b3f743a8f00'],
  '130009827'=>['size'=>7415640,'duration_ms'=>185391,'blob'=>'1a8cea5ad08073594885d70e6cd6b135e53a5320'],
  '107827229'=>['size'=>5498715,'duration_ms'=>135314,'blob'=>'84df01f5f29e66f08223d11a0fedf067a7ae6fb6'],
  '108422089'=>['size'=>4004093,'duration_ms'=>99997,'blob'=>'113714363c7107ab402dc7daf223ebd8cc93db7d'],
  '112047077'=>['size'=>3975881,'duration_ms'=>99291,'blob'=>'31ef93622246701a8749f42440645f01ce6307bd'],
  '114896393'=>['size'=>4515093,'duration_ms'=>112875,'blob'=>'257048105168e2099977be8635c5b16d826eeaa0'],
  '81936397'=>['size'=>5667988,'duration_ms'=>139546,'blob'=>'c087c217acf121a547c6120e2bc0745beb435abf'],
  '59759472'=>['size'=>7016534,'duration_ms'=>175308,'blob'=>'56498124d0c9eed08681c201d71f2b5675f44e50'],
  '123277830'=>['size'=>5143032,'duration_ms'=>128470,'blob'=>'962c40cd77412dc1be7162bfc4dde06827da36e2'],
  '83924496'=>['size'=>5721905,'duration_ms'=>143047,'blob'=>'cc7d50e27cf4a6be217ae773e7911915efb07ac8'],
  '59556187'=>['size'=>6723335,'duration_ms'=>165930,'blob'=>'adffd6222aba59b2f731723ab8948c4776af7b83'],
  '52765483'=>['size'=>5863363,'duration_ms'=>144405,'blob'=>'66e0d9d37d8c407c9c749db21c5f62fabdb4a6dc'],
  '124711308'=>['size'=>5055114,'duration_ms'=>126093,'blob'=>'abaa04d1d2d6ba2ebf354e88b3facb0d5f5d5d09'],
  '35758332'=>['size'=>8011908,'duration_ms'=>200072,'blob'=>'a10288add2ad77b58d860b23096e66ce3c4a9d65'],
  '143482533'=>['size'=>3845268,'duration_ms'=>96026,'blob'=>'0f289a1b14e1c6ac0dd572a538e6a8655996b784'],
  '53839022'=>['size'=>10863848,'duration_ms'=>271491,'blob'=>'acdeac236dcd8b0de5e3ceb0db4c5fe2437c3dec'],
  '116649706'=>['size'=>6287295,'duration_ms'=>155298,'blob'=>'00fc375b529206a87d3963772f68b0c9fce9cc16'],
  '89382788'=>['size'=>7721129,'duration_ms'=>192052,'blob'=>'25ee5aa7ea858db6fbae95e3fe69c70915095303'],
  '125539266'=>['size'=>3636288,'duration_ms'=>90906,'blob'=>'100390504b82516b405f86864ff717dec26d868c'],
  '89116734'=>['size'=>4275167,'duration_ms'=>176797,'blob'=>'5104d085430d86b4442407964096553311e4e2bc'],
  '68269714'=>['size'=>8749975,'duration_ms'=>218749,'blob'=>'d2f315603a78ebe0bb7d7cf7373199b418b60da8'],
  '148715970'=>['size'=>7257256,'duration_ms'=>179252,'blob'=>'2b291011fc0efa50e9ea08a98f13c773324fd269'],
  '136074520'=>['size'=>6494481,'duration_ms'=>161724,'blob'=>'e34612b3d84a2922a174d7b6a01cdd9d0d30c3f5'],
  '136101921'=>['size'=>4244190,'duration_ms'=>105718,'blob'=>'7c381dad0d931064f186b79e7e11cad75303a2cf'],
  '119296517'=>['size'=>5623437,'duration_ms'=>140251,'blob'=>'244030ec261a102c9cbe3c0b6d3d94ccc45330f1'],
  '70524316'=>['size'=>4935786,'duration_ms'=>122201,'blob'=>'61173702f72aede236b178df35adb415a57ab8c8'],
  '126276767'=>['size'=>5207771,'duration_ms'=>130194,'blob'=>'1ae7e84604c8ee2ad3c4555fc7b7eb62f0cce88e'],
  '70691077'=>['size'=>6940647,'duration_ms'=>171755,'blob'=>'5d9788246553ad48a2271c2f517ee15b63bd97dc'],
  '140257587'=>['size'=>4618493,'duration_ms'=>115357,'blob'=>'072958da827a12aefc6c1d695645e4eed21a499a'],
  '122053558'=>['size'=>4158484,'duration_ms'=>101930,'blob'=>'56f491b1f0e8c416e4ef7bd2daed0772b8270c0d'],
  '53582330'=>['size'=>7842573,'duration_ms'=>193985,'blob'=>'99121f43a94ee4ec576374cefa3b1bced9d1c441'],
  '45541231'=>['size'=>6356113,'duration_ms'=>158903,'blob'=>'4b27e45285110d9da6e2bbbea9bb604bee998ccd'],
  '97345805'=>['size'=>6132946,'duration_ms'=>151144,'blob'=>'c444f8abf2ceedc1441498016ad996ecd5a7ef32'],
  '122728371'=>['size'=>5198411,'duration_ms'=>129855,'blob'=>'7951e7b067a9d310f1d54dbb45ba5c3cb2020362'],
  '138578779'=>['size'=>4252516,'duration_ms'=>100023,'blob'=>'dc4adbdd9c9755865cddc7a0122620be5546fd7b'],
  '139803303'=>['size'=>3930631,'duration_ms'=>98220,'blob'=>'541fbcb71f5bd27358b97a11a70b1f3383e4f68d'],
  '114343051'=>['size'=>10145790,'duration_ms'=>252996,'blob'=>'3079009c681db3ddcd3c9549bf3cee46f9c638b0'],
  '135680515'=>['size'=>6570362,'duration_ms'=>164153,'blob'=>'869b28469db4d1914b3b2841c447fadcea1a93c8'],
  '97277436'=>['size'=>5852672,'duration_ms'=>145319,'blob'=>'d5eae7e92ca0a698ce82f819aa15bccc171fbee1'],
  '148628495'=>['size'=>11204530,'duration_ms'=>280111,'blob'=>'a9084be2708266a6117a1c79971b111c5aa80649'],
  '148716914'=>['size'=>10405093,'duration_ms'=>260127,'blob'=>'cbebbe418d2ddd8a3895098c3d2fc8a90b4ea1bb'],
  '38681475'=>['size'=>7103678,'duration_ms'=>175438,'blob'=>'a16ed8b9c0fb26d9bc7488130a67334b7ed3d0dc'],
  '21287095'=>['size'=>7768212,'duration_ms'=>192026,'blob'=>'f7ffa3ebe89bfb756e5af1dc6163d975c9da273c'],
  '109051375'=>['size'=>6373922,'duration_ms'=>159242,'blob'=>'b8b96d2e8abe27f4015f02d48e34ebdfbc655b36'],
  '104198618'=>['size'=>7447450,'duration_ms'=>184033,'blob'=>'944d0ee9fa4ad408cf1ea6650f7d1aef55aa1c90'],
  '106894275'=>['size'=>6033826,'duration_ms'=>146051,'blob'=>'0d851b42d8ccb5d9754cf8e5f3d0c4e73b7e9c48'],
  '103457320'=>['size'=>8377431,'duration_ms'=>208588,'blob'=>'abb839aae5760c1e9d6a16357e4de03ddbcf5fb5'],
  '53685449'=>['size'=>8579809,'duration_ms'=>212088,'blob'=>'9df248659933a3c99948a3f2076439f57c518aef'],
  '44950137'=>['size'=>7475662,'duration_ms'=>184738,'blob'=>'1af7cbb33d746dfbad0cb56907ffcc0761c1e45a'],
  '45564126'=>['size'=>6645991,'duration_ms'=>163971,'blob'=>'d9cc004b8f2d4b1b45c010433a813e0fcc241395'],
  '36161918'=>['size'=>9902960,'duration_ms'=>245420,'blob'=>'be4ea1c507d931a5ffc8f4a8dd39bbeb3278f50d'],
  '112218101'=>['size'=>6487377,'duration_ms'=>161541,'blob'=>'bb64dc6e9530252fe0c5a7cd142f848e62c8ee98'],
  '116357690'=>['size'=>5159061,'duration_ms'=>127791,'blob'=>'9b74df8402744099a23f647e254bd619335a897a'],
  '139046055'=>['size'=>5298735,'duration_ms'=>132467,'blob'=>'64fd3b8df64bce29a278ea3c63ccc87cd0bd1659'],
  '112035753'=>['size'=>6379752,'duration_ms'=>158851,'blob'=>'e735505850a052e2f7418e90808b90413bf26c46'],
  '139046046'=>['size'=>5543227,'duration_ms'=>138580,'blob'=>'f1cf26ffff4123b1ba053f4c9f37c3e1a441fa58'],
  '139046051'=>['size'=>5762656,'duration_ms'=>144065,'blob'=>'f9a25384140dd994bde8cef261103758f5eabc86'],
  '135706401'=>['size'=>5845658,'duration_ms'=>143360,'blob'=>'ebd0bd75826d10d40ef9b2264ca6ac53ae23bd29'],
  '62556361'=>['size'=>5969963,'duration_ms'=>147096,'blob'=>'8ae2d0eafa865b4a085f3081e0626e6dc98647ce'],
  '136101925'=>['size'=>3958932,'duration_ms'=>98586,'blob'=>'4c48245e3029f54a014c325a133cb56265cabf10'],
  '38681476'=>['size'=>5867564,'duration_ms'=>144536,'blob'=>'1060c9664935b2377e763068a4e3168851a4760e'],
  '140712545'=>['size'=>5512591,'duration_ms'=>137300,'blob'=>'060c62dcee272d7c75cc314060f321ebd8c33066'],
  '139046056'=>['size'=>8251603,'duration_ms'=>206289,'blob'=>'63a72ae2125785bf2a7739acb3ab2289c0a987ad'],
  '136267325'=>['size'=>4960175,'duration_ms'=>123899,'blob'=>'6f154dd8a475c7b2edaff5dcbf21b24c39c6728a'],
  '147953044'=>['size'=>4475341,'duration_ms'=>111882,'blob'=>'eb0ddfb875b776f730d4e4da68e073369883cc68'],
  '112045232'=>['size'=>4663423,'duration_ms'=>116480,'blob'=>'e84d8035905c3037571d4c8e66dc8b5bdc11604f'],
  '108857579'=>['size'=>6796671,'duration_ms'=>168986,'blob'=>'7b07bf3eae7076c652a09f188edae52924d37f87'],
  '53838987'=>['size'=>8163886,'duration_ms'=>198583,'blob'=>'4d981c8eb1ce4dc46acbbd06ea2809b4d3a402f1'],
  '114084879'=>['size'=>5473219,'duration_ms'=>136725,'blob'=>'f816c388e1e58b5bb34f570212bda01e34d600f7'],
  '81747372'=>['size'=>11699140,'duration_ms'=>290325,'blob'=>'df45b984643c44682fae441e1c18805ff3f0e76d'],
  '135590034'=>['size'=>5236028,'duration_ms'=>130795,'blob'=>'7eb8f1e2e5a0317131b46fdde41d3ed962f285cd'],
  '129054544'=>['size'=>5135404,'duration_ms'=>127896,'blob'=>'6f2ac5e0da5cfb36e0f242f3c995875c4238780a'],
  '132723443'=>['size'=>7371486,'duration_ms'=>183798,'blob'=>'db2fd9fee77653a5054128605896624fec9b19a9'],
  '138412039'=>['size'=>5080338,'duration_ms'=>126903,'blob'=>'c3183836ed50b283e7d48aab3a864811ea631857'],
  '119296533'=>['size'=>7297812,'duration_ms'=>177972,'blob'=>'b7575eebd1a1a792d80b072f18fccd4180dc4a6c'],
  '103844887'=>['size'=>5672139,'duration_ms'=>140904,'blob'=>'7db54fbdf1bd556204b588869387f3a87be4f84b'],
  '119923186'=>['size'=>5267897,'duration_ms'=>130952,'blob'=>'d60ab01bf952df410f6fb99c9a497204b4de82d5'],
  '133429866'=>['size'=>6685071,'duration_ms'=>164180,'blob'=>'7f54e9efcd45070bb303542b983b84bcab0b5590'],
  '148716915'=>['size'=>5383776,'duration_ms'=>132441,'blob'=>'fac3d948e56c691700bb8c80b6df18200d5c50ba'],
  '112996875'=>['size'=>13286298,'duration_ms'=>331233,'blob'=>'64154915abefd2f2e68e5b364598da2c74bb1bd7'],
  '84894428'=>['size'=>8819840,'duration_ms'=>212637,'blob'=>'8d842c91af0857737fc3f0d789956f4766582958'],
  '109996944'=>['size'=>5833708,'duration_ms'=>145842,'blob'=>'a28be188a37c8730d0400c20580dfa03b9031816'],
  '150820029'=>['size'=>3236763,'duration_ms'=>202292,'blob'=>'963619b7c417fed1a78fcc92876f9d99ef290d44'],
  '82890465'=>['size'=>8867444,'duration_ms'=>219507,'blob'=>'8f08f963e5032e347578496cfc675407f16c5cc7'],
  '149180232'=>['size'=>7363837,'duration_ms'=>181917,'blob'=>'fd0bd2d24b6cde727694ea676daf4980c90d7874'],
  '27323574'=>['size'=>11024136,'duration_ms'=>273450,'blob'=>'9c93cf417cea4e72361443a6ff4ee5b28c372694'],
  '46844318'=>['size'=>6651216,'duration_ms'=>164101,'blob'=>'499ef82707520397cc96b0d92061f8609793253c'],
  '46844319'=>['size'=>7741044,'duration_ms'=>191347,'blob'=>'fcf0f297d60095f63c9ef070f178e47d752d2e56'],
  '27317245'=>['size'=>11834954,'duration_ms'=>293695,'blob'=>'297ec41d1a74869c8bb319605bcdac84e5bccbf0'],
  '27323560'=>['size'=>10987542,'duration_ms'=>272509,'blob'=>'2105a93ea8dc8eec4d14e29f953134882926101a'],
  '46844320'=>['size'=>7066062,'duration_ms'=>174498,'blob'=>'25e70ee0d59e2b646a8cb0984597cb0d099da094'],
  '44368106'=>['size'=>9486046,'duration_ms'=>234998,'blob'=>'9237bf4954caa3e4da65d18553a3604d10313134'],
  '46844312'=>['size'=>6145507,'duration_ms'=>151484,'blob'=>'a29a5c24a72f9e252d8bede2b67cf0f04be9e48a'],
  '149171791'=>['size'=>5768299,'duration_ms'=>142054,'blob'=>'f38557866b10bad4ddcf1a3f49a5ded453758b8c'],
  '46844321'=>['size'=>9031515,'duration_ms'=>223634,'blob'=>'0e2a2ac3a355d530f09c6705839595d843df7aa4'],
  '77143804'=>['size'=>2231508,'duration_ms'=>90514,'blob'=>'b7d5919bbfbf6860f94cca6bdd92568e2e71183e'],
  '46844317'=>['size'=>6887384,'duration_ms'=>170031,'blob'=>'29a8524fbc112f1b96b88d5e2c86360cc1491a79'],
  '46844315'=>['size'=>8348152,'duration_ms'=>206550,'blob'=>'053c58166da8d1a56abcb3b19d2eb382cf56c33d'],
  '46844314'=>['size'=>8515335,'duration_ms'=>210730,'blob'=>'609792ec3d6cbcb45003bfa310e5c362f4b711de'],
  '123726329'=>['size'=>5292408,'duration_ms'=>132310,'blob'=>'03ee1fbef3ec6d91edf310cae972502a6aeab618'],
  '117219730'=>['size'=>5480685,'duration_ms'=>137016,'blob'=>'7ff5bd7a41736673391dabeb2b22f480cc449d2e'],
  '108721702'=>['size'=>8988673,'duration_ms'=>222563,'blob'=>'97aaea027d72494412118e99c35ad02fc5c47a55'],
  '105630453'=>['size'=>6021164,'duration_ms'=>148376,'blob'=>'ab6a5efa3674676048caaa83cf8d720a214f7db3'],
  '70975421'=>['size'=>5432886,'duration_ms'=>133669,'blob'=>'19c1b1f0eb153ef7c751507dd346880970926529'],
  '107970506'=>['size'=>4075564,'duration_ms'=>99736,'blob'=>'99f27921bda648448d7cfe2f38039bd729cce84c'],
  '78489534'=>['size'=>9983417,'duration_ms'=>247432,'blob'=>'c201c60ce7fca020c84508e1efbe5970e8377382'],
  '107970516'=>['size'=>5220772,'duration_ms'=>128366,'blob'=>'2b2e81cd42cd0b558f7a929e3385ae8e68aecb9a'],
  '133429873'=>['size'=>7801022,'duration_ms'=>192078,'blob'=>'9d2f845980b2e82d5b5419c571b4d916e0f12c55'],
  '107970523'=>['size'=>7928103,'duration_ms'=>196049,'blob'=>'196011e5c6f52baa6f8365134bfd0e00ef9f9610'],
  '133429868'=>['size'=>6443700,'duration_ms'=>158145,'blob'=>'a4b08e84fb8e9b83b575dab6247ca2e2fec37d7c'],
  '105333543'=>['size'=>7921106,'duration_ms'=>194194,'blob'=>'41fe1b041d35329658a65bc034687f2ad8ea7ef6'],
  '131794589'=>['size'=>5698102,'duration_ms'=>140069,'blob'=>'c730f5e6261e3cc50636e511dc18d1759156a34d'],
  '131794593'=>['size'=>6414902,'duration_ms'=>157989,'blob'=>'4b347d76991dac0c8da442b85fe74a2354693a55'],
  '145192519'=>['size'=>5851723,'duration_ms'=>145215,'blob'=>'a65d9f039a7c6656c460c94ac241300e8c0d04a2'],
  '145192511'=>['size'=>7833895,'duration_ms'=>194769,'blob'=>'4f007c942a38d454b3d66fdd7c4d3f7ec38240cd'],
  '78489537'=>['size'=>5906225,'duration_ms'=>145502,'blob'=>'120a630e91197b1e3b0261c01255bf1eff2692d8'],
  '131794600'=>['size'=>7342772,'duration_ms'=>181185,'blob'=>'050a7b136a5600bc6456dec20379d9707890a1ad'],
  '78489529'=>['size'=>4778780,'duration_ms'=>117316,'blob'=>'4c7ea82cf0b392f1bf10707f8c844c0389f49634'],
  '131794592'=>['size'=>9042821,'duration_ms'=>223687,'blob'=>'5803f5ed6783d3b1f7edea58058b297881fb5d36'],
  '145192512'=>['size'=>5451527,'duration_ms'=>135210,'blob'=>'7c692fa48e0d2af1d4bf72aeab932290b9ac8236'],
  '114440638'=>['size'=>6859130,'duration_ms'=>170553,'blob'=>'900ea0c2122ffbdd91e0be9469d948c228e06c6f'],
  '131794596'=>['size'=>12097058,'duration_ms'=>300042,'blob'=>'dcc46922c316a83319798f2397b0399d8ee2f4ec'],
  '114440643'=>['size'=>8439016,'duration_ms'=>210051,'blob'=>'edba6c31e941ddcc3de6193a412588fd04498757'],
  '117472918'=>['size'=>6110607,'duration_ms'=>152660,'blob'=>'0d08d7e9b7ed6eb01488e6b1feaad8a99c9b0473'],
  '119043915'=>['size'=>6779028,'duration_ms'=>168986,'blob'=>'df7b503ec733e60ed4775934b50a23c355a4ae80'],
  '95505944'=>['size'=>5929192,'duration_ms'=>146051,'blob'=>'e6a8b8809e8a1165e1fbc2cef7d2f15759410e85'],
  '40498601'=>['size'=>3465114,'duration_ms'=>140748,'blob'=>'5f63e6b5a00c834f1005d6872d0f57bb64811ff9'],
  '148610616'=>['size'=>4026285,'duration_ms'=>100656,'blob'=>'fd135d2f32e5b8f50fd203ef06e9f012e3153060'],
  '86505315'=>['size'=>11909143,'duration_ms'=>295549,'blob'=>'696b2eb0d232e80d292c64fd0957d386d7cb2e82'],
  '119258438'=>['size'=>9184384,'duration_ms'=>229120,'blob'=>'23a9f0efdd4897c51e0f506117716210035a1733'],
  '52397208'=>['size'=>8375318,'duration_ms'=>207229,'blob'=>'48126421efc7e7bc1cd094d9b9b531c729f6d6a2'],
  '149171789'=>['size'=>9687690,'duration_ms'=>240013,'blob'=>'ed0df7771c3a845169c768d74ad7b5c1e131bf7b'],
  '38436677'=>['size'=>11519416,'duration_ms'=>285832,'blob'=>'61cc23d0e55e2958fcbfb0a2d925f8295f9451b0'],
  '138562786'=>['size'=>4139679,'duration_ms'=>103079,'blob'=>'35ee54806a9d20bff28dfecd2dc77baa83349bd9'],
  '39779902'=>['size'=>6424265,'duration_ms'=>264046,'blob'=>'7026e3b37219edddf42e025d8b593b85247fd2fc'],
  '73939474'=>['size'=>9469305,'duration_ms'=>234553,'blob'=>'c7b5e1043d8591a84fb71c508f1259ca237728f2'],
  '138562779'=>['size'=>5313120,'duration_ms'=>132441,'blob'=>'e1e090e4876107f03d19ad4b122f1cd4a47cea77'],
  '93556488'=>['size'=>6228033,'duration_ms'=>153522,'blob'=>'59fc23c0baa69731564c14507979e5d953e7b3d7'],
  '112996867'=>['size'=>7555032,'duration_ms'=>187951,'blob'=>'dc16fc6b8e38f89fdd9c5f6faa54327efa3f9614'],
  '132723446'=>['size'=>5185559,'duration_ms'=>129149,'blob'=>'cd9331f460128a4baabddbbe618e93f65035b8bf'],
  '132723447'=>['size'=>6348531,'duration_ms'=>158224,'blob'=>'63df2259808e0fb3a6bfbb0853356eb988a9ecec'],
  '40498610'=>['size'=>4127788,'duration_ms'=>168359,'blob'=>'796dfae8e927219cb6deec84a4e97d8beb99ff0e'],
  '112996879'=>['size'=>8501731,'duration_ms'=>207909,'blob'=>'814a32d5c6202daf7778797086277f9627c97b84'],
  '92607045'=>['size'=>5118372,'duration_ms'=>125806,'blob'=>'440afa6c76ec73f70e41b75397f884b11f89d3fe'],
  '109051381'=>['size'=>5206770,'duration_ms'=>130064,'blob'=>'85dc6ef790e537b6a0e7704909769c42ee5753ec'],
  '60544538'=>['size'=>5795466,'duration_ms'=>142733,'blob'=>'6ad5507ec742839de13a9b418f35cfa0c4319597'],
  '118841491'=>['size'=>4321261,'duration_ms'=>107337,'blob'=>'cd23ad88a7053f36d64d5a41ac51edaf37a80497'],
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
    $out=['status'=>'NEW200_BATCH800_INDEPENDENT_READONLY','pass'=>$pass,'checked'=>200,
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
