package pro.celikom.nativeprobe.identitydiag;
public class TestSourceStateWatchdog {
 static int checks;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 public static void main(String[] args){
  SourceStateWatchdog w=new SourceStateWatchdog();
  check(!w.refresh("34",2,false,0,401627),"new-track buffering is initially tolerated");
  check(!w.refresh("34",2,false,2329,403956),"normal short transition does not reconnect");
  check(w.refresh("34",2,false,7375,409002),"recorded false buffering is refreshed rather than held until 504585ms");
  check(!w.refresh("34",2,false,12441,414068),"refreshes are rate limited");
  check(w.refresh("34",2,false,40000,449002),"a still-stale controller may be rechecked later");
  check(!w.refresh("34",3,true,646,505227),"recovered playing sample resets stalled state");
  check(!w.refresh("23",3,false,0,1137248),"pause immediately remains a pause");
  check(!w.refresh("23",3,false,6477,1143719),"short genuine pause is left alone");
  check(!w.refresh("23",3,false,11527,1148769),"owner-confirmed pause on Танцуй сама is left alone");
  check(!w.refresh("23",3,false,90000,1149000),"paused report cannot cause a refresh loop");
  SourceStateWatchdog normal=new SourceStateWatchdog();
  for(int i=0;i<300;i++)check(!normal.refresh("playing",3,true,i*1000,i*1000),"long healthy playing song never refreshes solely for event silence");
  check(!normal.refresh("paused",3,false,0,400000),"new pause starts its own deadline");
  check(!normal.refresh("paused",3,false,1,410000),"recent player event delays refresh");
  check(!normal.refresh("paused",3,false,9000,419000),"quiet genuine pause is never reconnected");
  for(int i=0;i<100;i++)check(!normal.refresh("paused",3,false,10000+i*1000,420000+i*1000),"owner-confirmed pause remains paused without watchdog reconnects");
  check(!normal.refresh("other",2,false,90000,420000),"new song does not inherit stale pause deadline");
  check(!normal.refresh(null,2,false,90000,430000),"missing source remains governed by source-unavailable handling");
  check(!normal.refresh("ended",4,false,90000,440000),"ended item remains governed by end handling");
  System.out.println("PASS: "+checks+" source-state watchdog / recorded Wi-Fi false-pause checks");
 }
}
