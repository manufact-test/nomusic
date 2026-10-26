package pro.celikom.nativeprobe.identitydiag;
import java.util.concurrent.*;
import org.json.JSONObject;
public class TestDiagnosticRequest {
 public static void main(String[] args)throws Exception{
  ExecutorService playback=Executors.newSingleThreadExecutor();DiagnosticRequest support=new DiagnosticRequest();
  CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1),done=new CountDownLatch(1);
  try{
   support.submit(playback,()->"token",token->{entered.countDown();if(!release.await(3,TimeUnit.SECONDS))throw new Exception("test_timeout");return new JSONObject();},(j,e)->done.countDown());
   if(!entered.await(2,TimeUnit.SECONDS))throw new AssertionError("support request did not begin");
   if(!"next-song".equals(playback.submit(()->"next-song").get(1,TimeUnit.SECONDS)))throw new AssertionError("support blocked playback");
   release.countDown();if(!done.await(2,TimeUnit.SECONDS))throw new AssertionError("missing support completion");
   CountDownLatch failed=new CountDownLatch(1);support.submit(playback,()->{throw new Exception("invalid_session");},token->{throw new AssertionError("request after auth failure");},(j,e)->{if(j==null&&"invalid_session".equals(e))failed.countDown();});
   if(!failed.await(2,TimeUnit.SECONDS))throw new AssertionError("auth failure not reported");
   CountDownLatch offline=new CountDownLatch(1);support.submit(playback,()->"token",token->{throw new Exception("private transport details");},(j,e)->{if(j==null&&"network_or_response_error".equals(e))offline.countDown();});
   if(!offline.await(2,TimeUnit.SECONDS))throw new AssertionError("network failure not reported");
   System.out.println("PASS: stalled diagnostics cannot block playback; auth and transport failures return actionable completion");
  }finally{release.countDown();playback.shutdownNow();support.network.shutdownNow();}
 }
}
