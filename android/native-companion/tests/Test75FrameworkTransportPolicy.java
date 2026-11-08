package pro.celikom.nativeprobe.identitydiag;
/** Pure host replay of owner-proven Test.74 good vs problematic native gesture cases. */
final class Test75FrameworkTransportPolicy {
 static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
 static YandexFrameworkTransportPolicy.Decision run(YandexFrameworkTransportPolicy p,
  String alias,String title,String artist,long duration,long remote,boolean remotePlaying,
  boolean available,int count,String witnessTitle,String witnessArtist,long witnessDuration,
  int state,long raw,long age,float speed,long t){
  return p.reconcile(alias,title,artist,duration,remote,remotePlaying,
   available,count,witnessTitle,witnessArtist,witnessDuration,state,raw,age,speed,t);
 }
 static void dymSeekAndPause(){
  YandexFrameworkTransportPolicy p=new YandexFrameworkTransportPolicy();
  String alias="371",title="Дым",artist="Лёша Свик";long duration=219660;
  YandexFrameworkTransportPolicy.Decision d=run(p,alias,title,artist,duration,3000,true,
    true,1,title,artist,duration,3,3000,0,1f,1000);
  check(!d.usePlatform&&!d.failClosed,"ordinary aligned sample remains Test73");
  d=run(p,alias,title,artist,duration,4000,true,true,1,title,artist,duration,
    3,61552,0,1f,2000);
  check(d.usePlatform&&d.firstRecovery&&d.seekObserved&&d.position==61552,
    "framework cursor immediately wins 3.2s early scrub");
  d=run(p,alias,title,artist,duration,4300,true,true,1,title,artist,duration,
    6,61552,50,0f,2050);
  check(d.usePlatform&&d.buffering&&!d.playing&&d.wantsToPlay,
    "buffering during real scrub is not misclassified as user pause");
  d=run(p,alias,title,artist,duration,5100,true,true,1,title,artist,duration,
    3,61700,100,1f,2600);
  check(d.usePlatform&&d.playing&&d.position==61800,
    "playing resumes with precise framework cursor");
  d=run(p,alias,title,artist,duration,62500,true,true,1,title,artist,duration,
    3,158017,0,1f,4000);
  check(d.usePlatform&&d.seekObserved&&d.position==158017,
    "second fast in-track seek is observed without waiting for Media3");
  d=run(p,alias,title,artist,duration,164000,true,true,1,title,artist,duration,
    2,162313,20,0f,8000);
  check(d.usePlatform&&!d.playing&&!d.buffering&&!d.wantsToPlay&&d.position==162313,
    "3.6s native pause must silence replacement even while Media3 playing");
  d=run(p,alias,title,artist,duration,165000,true,true,1,title,artist,duration,
    2,162313,3600,0f,11600);
  check(d.usePlatform&&!d.playing&&d.position==162313,
    "long native pause remains frozen while old remote advances");
  d=run(p,alias,title,artist,duration,165700,true,true,1,title,artist,duration,
    3,162313,0,1f,11800);
  check(d.usePlatform&&d.playing&&d.position==162313,
    "framework resume has no old remote clock drift");
  d=run(p,alias,title,artist,duration,166500,true,false,0,title,artist,duration,
    3,162313,0,1f,12100);
  check(d.failClosed&&!d.usePlatform,"permission revoked on authoritative song -> original only");
  d=run(p,"397","Розовое вино","Элджей, FEDUK",246810,100,true,
    false,0,null,null,-1,-1,-1,-1,1f,13000);
  check(!d.failClosed&&!d.usePlatform,"next track may safely use baseline without permission");
 }
 static void goodControlAndIdentitySafety(){
  YandexFrameworkTransportPolicy p=new YandexFrameworkTransportPolicy();
  String alias="123",title="Холодно",artist="Макс Корж";long duration=235000;
  YandexFrameworkTransportPolicy.Decision d=run(p,alias,title,artist,duration,1000,true,
    true,1,title,artist,duration,3,1000,0,1f,1000);
  check(!d.usePlatform,"good song initially stays original");
  d=run(p,alias,title,artist,duration,90000,true,
    true,1,title,artist,duration,3,90020,0,1f,1250);
  check(!d.usePlatform,"good native seek + Media3 seek together remains original");
  d=run(p,alias,title,artist,duration,95000,true,
    true,1,title,artist,duration,2,95000,0,0f,2000);
  check(d.usePlatform&&!d.playing&&d.firstRecovery,
    "native pause may correct missing Media3 state on any song");
  d=run(p,alias,title,artist,duration,98000,true,
    true,2,title,artist,duration,2,95000,300,0f,2400);
  check(d.failClosed,"multiple Yandex framework sessions must fail closed");
  p=new YandexFrameworkTransportPolicy();
  d=run(p,alias,title,artist,duration,1000,true,true,1,"Другая песня",
    artist,duration,2,90000,0,0f,1000);
  check(!d.usePlatform&&!d.failClosed,"wrong track NEVER controls CELIKOM");
  d=run(p,alias,title,artist,duration,1000,true,true,1,title,
    "Другой исполнитель",duration,2,90000,0,0f,1100);
  check(!d.usePlatform,"wrong artist denied");
  d=run(p,alias,title,artist,duration,1000,true,true,1,title,
    artist,duration+10000,2,90000,0,0f,1200);
  check(!d.usePlatform,"wrong duration denied");
  d=run(p,alias,title,artist,duration,1000,true,true,1,title,
    artist,duration,2,90000,400000,0f,1300);
  check(!d.usePlatform,"stale pause denied");
  d=run(p,alias,title,artist,duration,1000,true,true,1,title,
    artist,duration,6,90000,8000,0f,1500);
  check(!d.usePlatform,"stale buffering denied");
 }
 static void raskolSeekPause(){
  YandexFrameworkTransportPolicy p=new YandexFrameworkTransportPolicy();
  String title="Нас не понимают вообще",artist="RASKOL";long duration=232330;
  YandexFrameworkTransportPolicy.Decision d=run(p,"308",title,artist,duration,
    7000,true,true,1,title,artist,duration,3,52185,0,1f,1000);
  check(d.usePlatform&&d.seekObserved,"RASKOL seek immediately from native system");
  d=run(p,"308",title,artist,duration,10000,true,true,1,title,artist,duration,
    3,149441,0,1f,5000);
  check(d.usePlatform&&d.seekObserved,"RASKOL second seek");
  d=run(p,"308",title,artist,duration,152000,true,true,1,title,artist,duration,
    2,153584,20,0f,9000);
  check(!d.playing&&d.position==153584,"RASKOL actual pause");
  d=run(p,"308",title,artist,duration,153000,true,true,1,title,artist,duration,
    3,153584,0,1f,11000);
  check(d.playing&&d.usePlatform,"RASKOL resumes without remote pause flag");
 }
 public static void main(String[] a){
  dymSeekAndPause();goodControlAndIdentitySafety();raskolSeekPause();
  System.out.println("PASS Test75FrameworkTransportPolicy: no remote commands, verified session, selective seek/pause");
 }
}
