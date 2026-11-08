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
    '36161917'=>['size'=>5239559,'duration_ms'=>128810,'blob'=>'1433e28b553f961e781895efd827b10d1c52d322'],
    '106475674'=>['size'=>7873376,'duration_ms'=>189231,'blob'=>'ce9e854cfa81527f5a7c8d431648bbcf31af9515'],
    '66668867'=>['size'=>3234003,'duration_ms'=>131161,'blob'=>'2ebcc0870eccf8831748cb7328915bc015214023'],
    '48591809'=>['size'=>9500256,'duration_ms'=>237401,'blob'=>'277cd03a9f05a92491243ad82876494f4ba37910'],
    '138912048'=>['size'=>7139832,'duration_ms'=>178390,'blob'=>'3379d782452689b42430af19a13a601189bb2ac1'],
    '107769753'=>['size'=>12220544,'duration_ms'=>303360,'blob'=>'1b8724b1d92228474a1a60aecfbb0d795fc7ef13'],
    '90841991'=>['size'=>9175711,'duration_ms'=>227239,'blob'=>'91cbe290e6a61233eaa35c520beb3d30b929b84c'],
    '111454944'=>['size'=>10410759,'duration_ms'=>258090,'blob'=>'b26e90630fd8eaf9c06739531f0671562d84a49c'],
    '43854383'=>['size'=>6477784,'duration_ms'=>159791,'blob'=>'4a7fd20a9119c75dd45f35c38ba54d4d7bde7c8a'],
    '119890654'=>['size'=>3750705,'duration_ms'=>93022,'blob'=>'75627deabe52b08e889f19ca111c1fba221f3c45'],
    '79932386'=>['size'=>6556778,'duration_ms'=>163814,'blob'=>'69d7cab9a075abeb158a1f30fa64a525a3d29d81'],
    '120805927'=>['size'=>3880273,'duration_ms'=>96261,'blob'=>'e007e3dafdffcaeabf3bb62807c725b72f1cba56'],
    '130011719'=>['size'=>3674574,'duration_ms'=>91298,'blob'=>'08eac264eee8eea676710fa8abd9766c7dfeadd2'],
    '111124377'=>['size'=>5200418,'duration_ms'=>124918,'blob'=>'44206f9eed708ac99cc02de95b36694c73d71c7a'],
    '119890672'=>['size'=>7385216,'duration_ms'=>184320,'blob'=>'de518b3a09a7a41dae76cabce8f696bf00164bf9'],
    '52572387'=>['size'=>6955303,'duration_ms'=>171729,'blob'=>'ca8be59f58795b82cc2e1de004745559b8bf83a4'],
    '108050041'=>['size'=>6897491,'duration_ms'=>168333,'blob'=>'ea76f2b274f0699b54a395bb699e3142494b8ee8'],
    '69420850'=>['size'=>7069197,'duration_ms'=>174576,'blob'=>'11cd9f6b4bc1a4de8cc0bf43070008fcf4608b5c'],
    '67639975'=>['size'=>6406313,'duration_ms'=>160052,'blob'=>'7ffd6f349fff9e1d5f39086399e6536ae5190834'],
    '50400504'=>['size'=>5237491,'duration_ms'=>128784,'blob'=>'fa68b76d0f49278d1050d67ee95efa9ce31539d8'],
    '58978660'=>['size'=>6741099,'duration_ms'=>166374,'blob'=>'b329d1ffeaf77f16b251099e7f6df27555788776'],
    '58810179'=>['size'=>7767188,'duration_ms'=>192026,'blob'=>'88c44d85dac139bc9986fe9e085ffc45ca4dffa8'],
    '50573122'=>['size'=>9075401,'duration_ms'=>224731,'blob'=>'594661374fc0ce5a5bc8884eced3db6d003212d5'],
    '50400502'=>['size'=>7427597,'duration_ms'=>183536,'blob'=>'37651954bf3e78074660b6f0f4ab15c7fcd9def2'],
    '121733051'=>['size'=>4745971,'duration_ms'=>118544,'blob'=>'c57e6647b57ee735978febad5832165205de2e71'],
    '43503864'=>['size'=>5640821,'duration_ms'=>138867,'blob'=>'a5fb5435052d13a551c1b4b0eb1c6475a0e5803c'],
    '48592076'=>['size'=>8051401,'duration_ms'=>199131,'blob'=>'a3e90c20e3b7af858c4098fe91d827cd4cd20a57'],
    '81936387'=>['size'=>7616723,'duration_ms'=>188264,'blob'=>'3fa4636de01a91e36c9856c1e6ad093b891ae607'],
    '115258952'=>['size'=>6169644,'duration_ms'=>153496,'blob'=>'a9c9d478243e8f7d845c47622a5fa97ca55ce30d'],
    '131788963'=>['size'=>6331081,'duration_ms'=>158171,'blob'=>'68a2fe15b4ccb8e1acd868050d17659ac36e9867'],
    '87117636'=>['size'=>5145540,'duration_ms'=>126485,'blob'=>'4b3fa61f335549b01166802d3c1fef521dfa58b3'],
    '106123283'=>['size'=>4920886,'duration_ms'=>120869,'blob'=>'c4086047d664091e0c91a1700e235b0844f32be3'],
    '81936403'=>['size'=>9036740,'duration_ms'=>223765,'blob'=>'e4404dfbd176b0a1e0d706ad17bbb7ad6499eb19'],
    '38572740'=>['size'=>6980359,'duration_ms'=>172330,'blob'=>'c0fdb20f739eb338248409cf6d1e16790a1f17ad'],
    '48591482'=>['size'=>12297866,'duration_ms'=>305293,'blob'=>'36bac18fd8560454662bf371c91d5f01fe33b9cc'],
    '29851854'=>['size'=>8956261,'duration_ms'=>221727,'blob'=>'17c9428e0a34d498463346da6ba617e607d6eaef'],
    '117219737'=>['size'=>6736292,'duration_ms'=>168046,'blob'=>'c9fa2a910fd90cd241f9eca7727b9cbee8420fb5'],
    '36893518'=>['size'=>9418348,'duration_ms'=>234057,'blob'=>'3271e0bc3f00ae634b4702912d7e5d4000f95a26'],
    '140330884'=>['size'=>4611973,'duration_ms'=>114887,'blob'=>'30b849856008e45fbbaeccc4c9a7838949001236'],
    '142577327'=>['size'=>5391613,'duration_ms'=>134557,'blob'=>'7936d7dac30e8c9e65e2c4043d1c37ce552d67cb'],
    '29508050'=>['size'=>7246829,'duration_ms'=>179017,'blob'=>'70a28ab60cc945c9ca504808056e7c0f104256d0'],
    '36063268'=>['size'=>6604196,'duration_ms'=>162926,'blob'=>'2f040617efea04142976ed737e5c265d6137cc12'],
    '149220758'=>['size'=>5666943,'duration_ms'=>139520,'blob'=>'a3d912a2b0062d30f1e3e06892b6a9a0fbea162d'],
    '36562968'=>['size'=>6060849,'duration_ms'=>149342,'blob'=>'05c1efdeb20a720abfeea792a1d82eef8f05f731'],
    '115424575'=>['size'=>3643603,'duration_ms'=>90984,'blob'=>'ba26a54b8c13f86532ccee982264550ad7fe3c63'],
    '119280171'=>['size'=>5272829,'duration_ms'=>130717,'blob'=>'535a5ff02382da39ff81ac5854b3020ce0cc6ab1'],
    '35476145'=>['size'=>6808996,'duration_ms'=>168046,'blob'=>'72d64961ec3cce2d6f540c75da5ddb5183bd3615'],
    '117370317'=>['size'=>6785256,'duration_ms'=>169091,'blob'=>'16a9524961845aeb37620ff5f0388285c42c47f0'],
    '76711327'=>['size'=>9128670,'duration_ms'=>226038,'blob'=>'9346101adb0c1f42616b64956ceeba29bf9f4be4'],
    '116649704'=>['size'=>7623473,'duration_ms'=>190302,'blob'=>'ada468b4386f2a3a2175a6bcc88253898bb5375a'],
    '142825481'=>['size'=>6477366,'duration_ms'=>161829,'blob'=>'d50be3552d9c3d74e11158715101cf0e8bcdaef8'],
    '76711318'=>['size'=>9105703,'duration_ms'=>225489,'blob'=>'be95ae499d632b4e54ed998232e3eb7bde545593'],
    '132344550'=>['size'=>3867232,'duration_ms'=>94119,'blob'=>'bff931940ae15916673b54693055a6c478b53178'],
    '135256919'=>['size'=>5276277,'duration_ms'=>131187,'blob'=>'eb0a3078488b412ad556555ec552c6bd4ead536a'],
    '38180454'=>['size'=>4186303,'duration_ms'=>204957,'blob'=>'7f627411e05f260b143c3714d7e09784b86e5b0e'],
    '118111192'=>['size'=>5685710,'duration_ms'=>141218,'blob'=>'06dfb43cb2e2a562697fe9b01931eda749377864'],
    '110313505'=>['size'=>5795047,'duration_ms'=>144771,'blob'=>'3b30c9ba1528e84963ea2b990dd103267fa6223b'],
    '131866155'=>['size'=>3661366,'duration_ms'=>91429,'blob'=>'c87314826eeed1eb5a73353ac00d777c427c767e'],
    '113871254'=>['size'=>4817024,'duration_ms'=>120320,'blob'=>'c77e6f81a80127e12fd3956e817092b7913f23b0'],
    '73939476'=>['size'=>7554029,'duration_ms'=>186697,'blob'=>'4ff47a2c9fd0da17210163a3178e4609c518d0d5'],
    '98093044'=>['size'=>4580249,'duration_ms'=>112353,'blob'=>'0883415f15014013fb357b60309c71d34c4b3801'],
    '60441423'=>['size'=>6295972,'duration_ms'=>155246,'blob'=>'b3cdb2f49d79f53afdb65b438947345a91244794'],
    '58212468'=>['size'=>8498199,'duration_ms'=>212349,'blob'=>'25a6d1cfefb69928af16c1067e98443aaa3ed6bc'],
    '108485144'=>['size'=>5363581,'duration_ms'=>131579,'blob'=>'b3a6cb0f386b479919b5f4836d18589f5b015e22'],
    '109996934'=>['size'=>6143417,'duration_ms'=>151432,'blob'=>'ddb4ba4d3ad79097e739486bdafb98fda9b07564'],
    '31192330'=>['size'=>9468572,'duration_ms'=>234762,'blob'=>'913ceb7740821f954034d7746d0a2fd1ca7fdd3e'],
    '126043434'=>['size'=>4368094,'duration_ms'=>108278,'blob'=>'10d524d0640450f9675805daeaf29e3c7ba103fa'],
    '147603436'=>['size'=>7152657,'duration_ms'=>176744,'blob'=>'fd23272739a0cd4d95f02a113b300bbda76b4c48'],
    '38931996'=>['size'=>5849779,'duration_ms'=>144065,'blob'=>'3ee7f181c11fec684e229de1823942791c18acd0'],
    '135681115'=>['size'=>6645595,'duration_ms'=>166034,'blob'=>'c069c52add83b5d27d066f83d783fc76f47653ed'],
    '53582341'=>['size'=>4083042,'duration_ms'=>255190,'blob'=>'d3909aa15adb72b2d6ef09c391c6b2a866982749'],
    '51039981'=>['size'=>8758506,'duration_ms'=>214282,'blob'=>'4b04fc1b16b86f9b5d95048690d79608282be7e8'],
    '38563412'=>['size'=>8527165,'duration_ms'=>205662,'blob'=>'a8f3670818ad48747baa2b13387d821637953ff7'],
    '108977147'=>['size'=>5914584,'duration_ms'=>145711,'blob'=>'bc9db878c461a90b652ccf60153d084d6b43c9d6'],
    '139229968'=>['size'=>3578775,'duration_ms'=>89469,'blob'=>'3bc205385559c83a8cca4e4e55f2f12ac687af79'],
    '127455122'=>['size'=>5699962,'duration_ms'=>142393,'blob'=>'b5d3c7ec32b243690d114bb3d1a5572df0553a72'],
    '81936404'=>['size'=>6427608,'duration_ms'=>158511,'blob'=>'a00aaef196d0f538c020416118721e61311f5fde'],
    '116649702'=>['size'=>6018510,'duration_ms'=>150178,'blob'=>'faafa17a968df033e3dfd50a739ffeb9b81ded76'],
    '116649700'=>['size'=>4812698,'duration_ms'=>120033,'blob'=>'201ee7ced007d6512c9546f24f4620810419fc34'],
    '140330881'=>['size'=>3686193,'duration_ms'=>91742,'blob'=>'4a79ec4e8a59a11aed1cdcdf31755dbc24df7f1d'],
    '38419047'=>['size'=>13347968,'duration_ms'=>331520,'blob'=>'f2105c9d36fdb6fd503d1c5c20c08ec0da4b8c0d'],
    '136904439'=>['size'=>4033350,'duration_ms'=>100728,'blob'=>'55ed86d4c300c35e10723ab39eb3387f20e4e5c4'],
    '116649709'=>['size'=>6219130,'duration_ms'=>155193,'blob'=>'771643153ea447ed188778f92c4025caac1aa757'],
    '130919938'=>['size'=>4505581,'duration_ms'=>112457,'blob'=>'b3342925294ca75e135fe16f71c4c4f896fdeeb1'],
    '143244429'=>['size'=>6381564,'duration_ms'=>156630,'blob'=>'c14e1b12005c6dca0c61d73feedf6fb297781f7f'],
    '108127243'=>['size'=>7425507,'duration_ms'=>183484,'blob'=>'539445d315d77643b3a56a4edca6afab44799e35'],
    '130919974'=>['size'=>7088569,'duration_ms'=>177032,'blob'=>'a0a738c8862fdd0442833635c4b5b1144778894a'],
    '115308816'=>['size'=>5777055,'duration_ms'=>144039,'blob'=>'3efffc366edcbc24f742caf8936b26545a822ae9'],
    '43528291'=>['size'=>8853882,'duration_ms'=>219193,'blob'=>'373b28a6adc1871b6251f930b1b4a8ddb1714481'],
    '130919941'=>['size'=>5153480,'duration_ms'=>128731,'blob'=>'a137848d3c0880ada5cc5c54a1100c6b45600c9b'],
    '138413377'=>['size'=>5061154,'duration_ms'=>125962,'blob'=>'99aaa21ffa8ee34aa174339564e1124d6812c40b'],
    '108284700'=>['size'=>6448108,'duration_ms'=>161097,'blob'=>'72b81b2ed0742a54af4356df945524f73471d5de'],
    '110023304'=>['size'=>2720957,'duration_ms'=>67918,'blob'=>'dbaede9014b201acae08faa820d0f4aedf3be963'],
    '120305626'=>['size'=>5998155,'duration_ms'=>149055,'blob'=>'da07bf494e23670733a6e8ab132b134523dfa262'],
    '83836715'=>['size'=>5833709,'duration_ms'=>145842,'blob'=>'ee91e1fd9e74c18709014abd68e3450374739459'],
    '104242342'=>['size'=>4005556,'duration_ms'=>97985,'blob'=>'73659a17e2e3967f8e5a6ac5a2062e6f3f353af5'],
    '48592086'=>['size'=>9487091,'duration_ms'=>235024,'blob'=>'e1cbb57fef60f3c4e562d35fdfdaf9401c82227a'],
    '41468696'=>['size'=>7806874,'duration_ms'=>192993,'blob'=>'dac05825eeefc13e96b0886a8064bbf44c2718d3'],
    '105382858'=>['size'=>4695815,'duration_ms'=>117394,'blob'=>'aca1e6dd2159cde3138010a9c356002c0efb08cd'],
    '105382841'=>['size'=>6290748,'duration_ms'=>155115,'blob'=>'9eac745a908ac01db1ef5207f310e0072f92e3e3'],
    '105382847'=>['size'=>6586454,'duration_ms'=>162508,'blob'=>'5dc7f800dea68051fa8740ec82b9438df60413fd'],
    '105382856'=>['size'=>6345082,'duration_ms'=>156473,'blob'=>'c9e5e2d0d0457641e362455eee4d41eacd695333'],
    '106018754'=>['size'=>5354518,'duration_ms'=>131709,'blob'=>'d55c3d12a87300b502f3aff756f3635add24c673'],
    '80159693'=>['size'=>5796075,'duration_ms'=>139259,'blob'=>'5622498004c93ad81905d6363aa8bc11cb864af8'],
    '93556490'=>['size'=>6551972,'duration_ms'=>161646,'blob'=>'aed2533458c97588ac89d99d0574342d032eb6db'],
    '119280163'=>['size'=>4205988,'duration_ms'=>104046,'blob'=>'d20c6a74529848dbcdc9f86c60a36a806174f09b'],
    '105382852'=>['size'=>5760964,'duration_ms'=>141845,'blob'=>'8f0a56fadad964eb37b7dd2a180881a77df3995a'],
    '104242332'=>['size'=>4129899,'duration_ms'=>101094,'blob'=>'99a915e1665bc046a0f94ff1b78b9fc0f68f33a3'],
    '104242353'=>['size'=>6101157,'duration_ms'=>147749,'blob'=>'294356eb41fa3f040bb95fd3e9cc5c593982b640'],
    '105999154'=>['size'=>5772060,'duration_ms'=>144196,'blob'=>'64d37bacb22f656edaf899e5a2156a64889dcf45'],
    '97933934'=>['size'=>6772445,'duration_ms'=>167158,'blob'=>'9120419833b12029212e4bfcec285642941a12be'],
    '137300020'=>['size'=>3598464,'duration_ms'=>89600,'blob'=>'c321f59d1271d04f16ab60e5514aaaf84d0b735c'],
    '144098512'=>['size'=>5691557,'duration_ms'=>140852,'blob'=>'b0141e2fb5d2639e05ea6ab5747b85a7c18467e7'],
    '119923201'=>['size'=>7512338,'duration_ms'=>187063,'blob'=>'2144fb1dfdf34ba39a4c33f5186cbd234588b67f'],
    '123874951'=>['size'=>5979723,'duration_ms'=>149055,'blob'=>'bad486772b372a48382202a1d12d054890c25940'],
    '38149234'=>['size'=>6466291,'duration_ms'=>159504,'blob'=>'a1c220083d0760e31a8f44ea03563f5326166841'],
    '139228490'=>['size'=>3736599,'duration_ms'=>93309,'blob'=>'4653ae81e3c0543c26c305f24939f6bfecf3199d'],
    '137803949'=>['size'=>5986682,'duration_ms'=>147513,'blob'=>'95264633c5be28f02be29a9c8b7769fb04fc83a3'],
    '148781606'=>['size'=>7148147,'duration_ms'=>178704,'blob'=>'71b715c73a65231d6fe95e69ff72304e8717a4c3'],
    '148778065'=>['size'=>6618510,'duration_ms'=>165460,'blob'=>'a51469cb5fca7b2657d56d57052464550fd148e3'],
    '137251857'=>['size'=>4347380,'duration_ms'=>103654,'blob'=>'6a6cad73de6aeee25b253a775b61b5ba689c74c6'],
    '81772338'=>['size'=>4373987,'duration_ms'=>109244,'blob'=>'49499ba76401f556170d7dd9fd23587d32eb3dff'],
    '68074242'=>['size'=>2842166,'duration_ms'=>114834,'blob'=>'010ff4a92dca81acb51803a3caf8c18fbe32d398'],
    '123286436'=>['size'=>5242151,'duration_ms'=>130769,'blob'=>'57c11732679fb35f3153c61e28d02b38d6a4d4a2'],
    '131538268'=>['size'=>6788119,'duration_ms'=>167549,'blob'=>'711c0df9205405c7202d9a37dd9a508bf8172e52'],
    '42840670'=>['size'=>7183070,'duration_ms'=>177398,'blob'=>'c63586da3a4aba8426b4997a1647a2cc0f467be6'],
    '131898079'=>['size'=>6490532,'duration_ms'=>159086,'blob'=>'89dc0f8680127d2e4ab81002387151dba31a55f9'],
    '147212188'=>['size'=>1678315,'duration_ms'=>37512,'blob'=>'7afc8e598b5ec55d228c9a9e4ce2ae0dcb4b7f8a'],
    '107845498'=>['size'=>8272919,'duration_ms'=>204669,'blob'=>'5e81c74b50f0972e1ccd0f3e73d3c59d52951859'],
    '122852454'=>['size'=>6108058,'duration_ms'=>152033,'blob'=>'39cdd52da21c3c3869250fa419079487978280be'],
    '100923878'=>['size'=>8057252,'duration_ms'=>201326,'blob'=>'0aae2e203602ba5b22e6c86325995e7aca75a56b'],
    '60968632'=>['size'=>9510078,'duration_ms'=>235598,'blob'=>'7226ae2b25ea99f843e3b5ae462dbc0720f6b88e'],
    '139671870'=>['size'=>7057588,'duration_ms'=>174785,'blob'=>'95f97c220cbfbe869136df26b1e2fef92dbb4eee'],
    '121043176'=>['size'=>4125301,'duration_ms'=>103027,'blob'=>'2e6d20444de39841f5365790feacd543f4ef93f1'],
    '130751236'=>['size'=>5311072,'duration_ms'=>132441,'blob'=>'3f7b7032e26888d4f2d6e419f78023cfbb95ec84'],
    '147212189'=>['size'=>7057235,'duration_ms'=>169378,'blob'=>'11923701aeef003beb2070612664c661cd892d2d'],
    '145536333'=>['size'=>4776900,'duration_ms'=>118805,'blob'=>'fb6ae74730269dcdbbe4735f9f7d510dc6be6635'],
    '54281103'=>['size'=>5838307,'duration_ms'=>143804,'blob'=>'d08648d70804ed0b94e897b821b63bf0157e62c6'],
    '136260233'=>['size'=>4094999,'duration_ms'=>102269,'blob'=>'91c6ab37782f4ba3f93b3fdcb2bf4501fd0cdb31'],
    '140701188'=>['size'=>4017677,'duration_ms'=>100336,'blob'=>'af09c4267ce0c5e4126091e3578b9fdc6581d200'],
    '145536338'=>['size'=>6076891,'duration_ms'=>148872,'blob'=>'87f6be2e84c4e73204a20a7756eb172ce8734101'],
    '142512577'=>['size'=>4794035,'duration_ms'=>119850,'blob'=>'18daeeee2b48ec4fd1914bb5d3b7a2fb26e39a53'],
    '117383616'=>['size'=>6330036,'duration_ms'=>158250,'blob'=>'ac23df34ab8afad5de8e78ac0c5c7c31fc79c1b7'],
    '147212190'=>['size'=>13276915,'duration_ms'=>329744,'blob'=>'40d89a4efdabf6484d43a61e1880502b8a677c95'],
    '141390024'=>['size'=>3801383,'duration_ms'=>94929,'blob'=>'d93ce820312c94cea14cfaef615a084baaa4fc34'],
    '136021421'=>['size'=>6045824,'duration_ms'=>151040,'blob'=>'f5a13bfaa97aa99a509d02c5f11555668eb16432'],
    '25738208'=>['size'=>6809016,'duration_ms'=>168072,'blob'=>'41ac3a30f361dfd1c88c3e9055349f05d0299d15'],
    '148716941'=>['size'=>9365212,'duration_ms'=>227997,'blob'=>'51592b944aa2c6dc691f85ec33809bc11605cfac'],
    '135463527'=>['size'=>5023912,'duration_ms'=>125597,'blob'=>'3bb5edfe07fc6102daa3286b0f0df760a6a22d9b'],
    '39151536'=>['size'=>11054437,'duration_ms'=>274207,'blob'=>'6a4a223771441bfc42fc4c03c1862459c3219ad0'],
    '131394968'=>['size'=>9503424,'duration_ms'=>237480,'blob'=>'4aa3a68c85fcf4642b75df3b3074434e8016ee55'],
    '66668863'=>['size'=>3077268,'duration_ms'=>124630,'blob'=>'e9179bda4ba36944c6a48f1bb0fdcde8e722cdbb'],
    '137950219'=>['size'=>8208762,'duration_ms'=>205113,'blob'=>'5e5e52690fa666d9c92bc685dc3a9c3e2fa1351a'],
    '146183038'=>['size'=>3976395,'duration_ms'=>94354,'blob'=>'7b08f353bc55be070a923df6260c96b479704c70'],
    '139083707'=>['size'=>4160452,'duration_ms'=>103445,'blob'=>'433422f846c0eaaaad5f93a61731d3b459f5e37d'],
    '62484718'=>['size'=>7850362,'duration_ms'=>196153,'blob'=>'eaef946d19970638484e4dd76be6feefae684fb7'],
    '81750768'=>['size'=>6224919,'duration_ms'=>153469,'blob'=>'182d4e572924aa33194e2747410b8de42760e4ed'],
    '93012495'=>['size'=>4363956,'duration_ms'=>106945,'blob'=>'0278041f00a38335d44b3f3b00022ef10f43c336'],
    '95699210'=>['size'=>4371270,'duration_ms'=>107128,'blob'=>'35c4552c1a214f8d212da720b97c72243bf9a9eb'],
    '104182086'=>['size'=>4857498,'duration_ms'=>117656,'blob'=>'6d1141277b823756431fc6d68acc3e96cfa62a62'],
    '66801291'=>['size'=>3960625,'duration_ms'=>161437,'blob'=>'f01c09adcf02b9824e2befc523de678cb4bd4787'],
    '137709368'=>['size'=>5928795,'duration_ms'=>148114,'blob'=>'3f1b541d9573ee619bbbb8c56e00dbbdb049a8fa'],
    '125535661'=>['size'=>5134756,'duration_ms'=>127086,'blob'=>'53ae81ef6bddd128c0b66889dc6bd425a143fb64'],
    '35681868'=>['size'=>8994448,'duration_ms'=>220656,'blob'=>'5521a3e0a88c31f259f978e67cd67c6ec6f55aff'],
    '108523845'=>['size'=>5940707,'duration_ms'=>146364,'blob'=>'bc26cb254eaebd619d1219768c861d5b9ba33fbd'],
    '84106658'=>['size'=>6147659,'duration_ms'=>152895,'blob'=>'f84fb40a21ba0c37c60f7a2e54786885663b5548'],
    '104735373'=>['size'=>4493523,'duration_ms'=>110184,'blob'=>'fbbc443623dc08e88a9590f1e77366c3cd843791'],
    '125535648'=>['size'=>4501568,'duration_ms'=>112104,'blob'=>'45ee286fee2fbd0cf9b60d742701cdb1561dc06e'],
    '36142276'=>['size'=>3691532,'duration_ms'=>89861,'blob'=>'2e880ebec9fbad845b9126e471b37654dd2c7c61'],
    '36161896'=>['size'=>9772975,'duration_ms'=>244219,'blob'=>'1cc05795f48b6d67d15ac3e6c6f3a8b7381dac91'],
    '110058012'=>['size'=>7489872,'duration_ms'=>187141,'blob'=>'542665e74668501d4e2b8b334f4b7e75817f5f55'],
    '118663870'=>['size'=>5832276,'duration_ms'=>140251,'blob'=>'fcc5bec37299d8060757902fa52a2ccb3f91ffbc'],
    '96941368'=>['size'=>5010041,'duration_ms'=>123037,'blob'=>'526a181c267c0628b108a1f20c0dc6eb36cf1b80'],
    '28676494'=>['size'=>8413959,'duration_ms'=>208170,'blob'=>'d8af07a3d8b94ecc74a18dd5b3b593ac9ad5e9b0'],
    '135256913'=>['size'=>5464359,'duration_ms'=>135889,'blob'=>'ddf8ac9fd371cdec78826ae28e1af59a719bcec2'],
    '135256916'=>['size'=>5260604,'duration_ms'=>130795,'blob'=>'c33697f4f9353369bb0fd8672224e0f070ad3cbe'],
    '135256920'=>['size'=>4899069,'duration_ms'=>121757,'blob'=>'5b80ea2a6c1e830ab5a2badc61cf1db08b8e0f6a'],
    '135256909'=>['size'=>6358791,'duration_ms'=>158250,'blob'=>'c38f10727dfb670d058bb98ad9a5c374b614ca0c'],
    '119469048'=>['size'=>5026003,'duration_ms'=>125544,'blob'=>'7cfa02eaacab59db61684df9ac4c5231f58f841a'],
    '110997060'=>['size'=>8257505,'duration_ms'=>203233,'blob'=>'546cb27b037573000ae7c0134473fcce9229323d'],
    '135256921'=>['size'=>4625306,'duration_ms'=>114913,'blob'=>'f397d865d12976504174cf4035d0a309a3c691e5'],
    '119469050'=>['size'=>5065709,'duration_ms'=>126537,'blob'=>'c004240b3b3dd5cf2a3a359636115a917efa9820'],
    '35758333'=>['size'=>5250237,'duration_ms'=>218279,'blob'=>'ab69b3428e5dea3cecb1f239f18e30eaa440fbb4'],
    '147993029'=>['size'=>5494849,'duration_ms'=>136882,'blob'=>'39fc40e9bd85597a488ce4c5a4ff4832c6e84d35'],
    '119469051'=>['size'=>6274859,'duration_ms'=>153365,'blob'=>'d9f1bef11c0de1538e90c22db58dc6e61babcd35'],
    '131538266'=>['size'=>5687842,'duration_ms'=>140042,'blob'=>'ca041e1b34ce34a00783f31a212c349dfb12685f'],
    '131538273'=>['size'=>5172707,'duration_ms'=>127164,'blob'=>'670e1b8c8dec639d330da35be609ca914af5e9ff'],
    '131538269'=>['size'=>6708707,'duration_ms'=>165564,'blob'=>'6c6484ca4a9ea6d06a477187bd831577cbafea92'],
    '131538276'=>['size'=>4887450,'duration_ms'=>120033,'blob'=>'b495abcd0f7443792e86acc943b69391d509081d'],
    '131538271'=>['size'=>5368103,'duration_ms'=>132049,'blob'=>'470fa93d2469d836a53fe3642c1eefa3dc323d68'],
    '76262072'=>['size'=>6274029,'duration_ms'=>154697,'blob'=>'6cc23dfff763ae4a633e8fa8fbf5b24f34f4f57e'],
    '76262126'=>['size'=>5517523,'duration_ms'=>135784,'blob'=>'318fa1bf17b415bf3712a5225406f252a7c3681e'],
    '76262124'=>['size'=>6648103,'duration_ms'=>164049,'blob'=>'a7cc909358ba3759829d887ae08e8ab36742b300'],
    '76262104'=>['size'=>6143417,'duration_ms'=>151432,'blob'=>'0910db4c4d0d30d282916ad68706cebe8aac8ad2'],
    '131538277'=>['size'=>6140282,'duration_ms'=>151353,'blob'=>'d2158a11b964261d58ec4d9cfe78afd0e35a449c'],
    '64724076'=>['size'=>4558686,'duration_ms'=>112065,'blob'=>'da49262e695a4b84dd8d211e6391379b040c074a'],
    '76262139'=>['size'=>5533197,'duration_ms'=>136176,'blob'=>'e3f76ca8fb54580a96bfa2e45223c3be1e4f30b2'],
    '104896796'=>['size'=>3426264,'duration_ms'=>85551,'blob'=>'89d943857745ffa93fa2d8b476a3a7129c35ab2e'],
    '130642855'=>['size'=>2784697,'duration_ms'=>69512,'blob'=>'3b78c7e482c5b2dfdaf66a30a1c435dc83349838'],
    '116486249'=>['size'=>6247384,'duration_ms'=>155951,'blob'=>'332dbc4f6a7283a48a487d3b1e5bb1f005ac7dd7'],
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
    $verified=0;$absent=0;$bytes=0;$issues=[];$batch=[0,0,0,0];$ids=[];
    $pdo->exec('START TRANSACTION READ ONLY');
    foreach($expected as $id=>$e){
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
        $index=count($ids);$batch[intdiv($index,50)]++;
        $ids[]=['track_id'=>$id,'replacement_id'=>(int)$r['id']];
    }
    $pdo->rollBack();
    $pass=count($expected)===200 && $verified===200 && $absent===200
          && $batch===[50,50,50,50] && !$issues;
    $out=['status'=>'LIVE200_INDEPENDENT_READONLY','pass'=>$pass,'checked'=>200,
          'pending'=>$verified,'files_verified'=>$verified,'private_bytes'=>$bytes,
          'batch_counts'=>$batch,'catalogue_absent'=>200-count($issues),
          'resolve_not_found'=>$absent,'auto_approved'=>0,'active'=>0,
          'writes'=>0,'issues'=>$issues,'records'=>$ids];
    echo json_encode($out,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),"\n";
    if(!$pass)exit(1);
}catch(Throwable $e){
    if($pdo instanceof PDO&&$pdo->inTransaction())$pdo->rollBack();
    fwrite(STDERR,'LIVE200_INDEPENDENT_AUDIT_REFUSED: '.$e->getMessage()."\n");
    exit(2);
}
