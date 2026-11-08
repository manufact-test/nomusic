package pro.celikom.nativeprobe.identitydiag;
final class Test76YandexIdentityDivergenceGate {
 static void ck(boolean ok,String why){if(!ok)throw new AssertionError(why);}
 static boolean see(YandexIdentityDivergenceGate g,long t,int oldState,
   boolean oldPlaying,long eventAge,boolean available,int count,
   String oldTitle,String oldArtist,String newTitle,String newArtist,long duration,
   int platformState,long age){
   return g.observe("504",oldTitle,oldArtist,duration,oldState,oldPlaying,eventAge,
     available,count,newTitle,newArtist,duration,platformState,5000,age,t);
 }
 public static void main(String[] args){
  YandexIdentityDivergenceGate g=new YandexIdentityDivergenceGate();
  ck(!see(g,0,2,false,1600,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,0),"first mismatch only records evidence");
  ck(!see(g,550,2,false,2150,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,100),"no premature release/probe");
  ck(see(g,1150,2,false,2700,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,20),"Test75 t16.5+ one-second stable mismatch permits *probe only*");
  ck(g.mismatchActive(),"UI may show stale source rather than blame Yandex");
  ck(!see(g,1800,2,false,3400,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,30),"bound probes despite every tick");
  ck(see(g,7000,2,false,8600,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,0),"bounded retries of still-mismatched source");
  ck(!see(g,7500,2,false,9100,true,1,"Дым","Лёша Свик",
    "Дым","Лёша Свик",219660,3,0),"fresh same identity clears gate");
  ck(!g.mismatchActive(),"no stale label after recovery");
  g=new YandexIdentityDivergenceGate();
  ck(!see(g,0,3,true,9999,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,0),"normal playing remote is never recycled");
  ck(!see(g,1000,3,true,9999,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,0),"persisting healthy playing mismatch is still NOT enough to recycle");
  g=new YandexIdentityDivergenceGate();
  ck(!see(g,0,2,false,120,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,0),"fresh remote transition needs settling time");
  ck(!see(g,2000,2,false,2000,false,0,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,0),"no permission => never probe");
  ck(!see(g,3000,2,false,3000,true,2,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,0),"two Yandex sessions are ambiguous");
  ck(!see(g,4000,2,false,4000,true,1,"Биг сити лайф","Триагрутрика",
    "Дым","Лёша Свик",219660,3,10000),"stale system playback state denied");
  ck(!YandexIdentityDivergenceGate.sameTrack("Биг сити лайф","Триагрутрика",210000,
    "Дым","Лёша Свик",219660),"identity mismatch not authorized as same-song seek");
  ck(YandexIdentityDivergenceGate.sameTrack(" Дым "," ЛЁША СВИК ",219660,
    "дым","лёша свик",219700),"same fresh song tolerant to insignificant formatting and duration");
  System.out.println("PASS Test76YandexIdentityDivergenceGate: safe non-destructive detection, cooldown, permissions, healthy-song fence");
 }
}
