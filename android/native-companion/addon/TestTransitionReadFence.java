package pro.celikom.nativeprobe.identitydiag;
import java.net.*;
import java.util.concurrent.atomic.*;
public class TestTransitionReadFence {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 public static void main(String[] args)throws Exception{
  float previous=0;for(int i=0;i<=36;i++){float mix=TransitionMix.progress(i*10,360);check(mix>=previous&&mix>=0&&mix<=1,"smooth monotonic complementary fade");previous=mix;}
  check(TransitionMix.progress(-10,360)==0&&TransitionMix.progress(500,360)==1,"late handler clamps fade endpoints");check(TransitionMix.progress(90,360)<0.2&&TransitionMix.progress(270,360)>0.8,"fade has gentle endpoints");
  AtomicBoolean valid=new AtomicBoolean(true),disconnected=new AtomicBoolean(false);HttpURLConnection c=new HttpURLConnection(new URL("https://localhost/resolve")){public void disconnect(){disconnected.set(true);}public boolean usingProxy(){return false;}public void connect(){}};
  try(ReadFence fence=new ReadFence(c,valid::get)){fence.check();valid.set(false);long start=System.nanoTime();while(!disconnected.get()&&(System.nanoTime()-start)/1000000<1500)Thread.sleep(10);check(disconnected.get(),"obsolete read socket is cancelled promptly");try{fence.check();throw new AssertionError("stale lookup accepted");}catch(java.io.IOException e){check(e.getMessage().equals("lookup_cancelled"),"late read result is rejected");}}
  disconnected.set(false);try(ReadFence fence=new ReadFence(c,null)){fence.check();Thread.sleep(150);check(!disconnected.get(),"ordinary authentication and write requests are not cancelled");}
  valid.set(true);ReadFence finished=new ReadFence(c,valid::get);finished.close();valid.set(false);Thread.sleep(150);check(!disconnected.get(),"completed request cancels its obsolete watcher");
  System.out.println("PASS: "+checks+" transition curve and obsolete read cancellation checks");
 }
}
