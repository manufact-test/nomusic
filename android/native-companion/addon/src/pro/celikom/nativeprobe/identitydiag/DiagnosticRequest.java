package pro.celikom.nativeprobe.identitydiag;
import java.util.concurrent.*;
import java.util.function.BiConsumer;
import org.json.JSONObject;
/** Only token rotation uses the playback queue; support network waits never do. */
final class DiagnosticRequest {
 interface Request {JSONObject get(String token)throws Exception;}
 final ExecutorService network=Executors.newSingleThreadExecutor();
 void submit(Executor auth,Callable<String> token,Request request,BiConsumer<JSONObject,String> result){
  auth.execute(()->{try{String access=token.call();network.execute(()->{try{result.accept(request.get(access),null);}catch(Exception e){result.accept(null,error(e));}});}catch(Exception e){result.accept(null,error(e));}});
 }
 static String error(Exception e){String s=e.getMessage();return s!=null&&s.matches("[a-z0-9_]{1,80}")?s:"network_or_response_error";}
}
