package pro.celikom.nativeprobe.identitydiag;
import org.json.*;import java.util.*;
public class TestContracts {
 static int tests;static void ok(boolean b,String reason){tests++;if(!b)throw new AssertionError(reason);}
 static void rejects(JSONObject d,long now,String reason)throws Exception {boolean bad=false;try{ApiContract.audio(d,now);}catch(Exception e){bad=true;}ok(bad,reason);}
 static JSONObject copy(JSONObject j)throws Exception{return new JSONObject(j.toString());}
 public static void main(String[] args)throws Exception {
  long now=System.currentTimeMillis(),expires=now/1000+600;String query="expires="+expires+"&token="+String.join("",Collections.nCopies(64,"a"));JSONObject good=new JSONObject().put("found",true).put("replacement_id",7).put("version",1).put("duration_ms",183720).put("expires_at",expires).put("gain_db",0).put("mime_type","audio/mpeg").put("audio_url","/api/v1/audio/7?"+query);
  ok(ApiContract.audio(good,now).startsWith(ApiContract.ORIGIN+"/api/v1/audio/7?"),"same-origin signed audio");
  rejects(copy(good).put("audio_url","https://evil.example/api/v1/audio/7?"+query),now,"cross-origin audio");
  rejects(copy(good).put("audio_url","http://darkred-camel-588676.hostingersite.com/api/v1/audio/7?"+query),now,"cleartext audio");
  rejects(copy(good).put("audio_url","/api/v1/audio/7?"+query+"&token="+String.join("",Collections.nCopies(64,"b"))),now,"duplicate query token");
  rejects(copy(good).put("audio_url","/api/v1/audio/7?"+query+"&other=x"),now,"unknown query");
  rejects(copy(good).put("audio_url","/api/v1/audio/8?"+query),now,"wrong replacement");
  rejects(copy(good).put("audio_url","/api/v1/audio/7?"+query+"#fragment"),now,"fragment");
  rejects(copy(good).put("audio_url","/api/v1/audio/7?"+query+"&sid=0"),now,"invalid session");
  rejects(copy(good).put("expires_at",now/1000-1),now,"expired descriptor");rejects(copy(good).put("expires_at",now/1000+4000),now,"excessive authorization TTL");
  rejects(copy(good).put("gain_db",13),now,"gain bound");rejects(copy(good).put("mime_type","text/html"),now,"unsupported media");
  rejects(copy(good).put("replacement_id","7"),now,"string ID rejected");rejects(copy(good).put("duration_ms",183720.5),now,"fractional duration rejected");
  ok(ApiContract.durations(183720,184000,184010),"duration tolerance");ok(!ApiContract.durations(183720,200000,200000),"wrong edition duration");ok(!ApiContract.durations(183720,183720,180000),"truncated file");ok(!ApiContract.durations(0,183720,183720),"missing source duration");
  ok(ApiContract.current("a","a",500,true),"current source");ok(!ApiContract.current("a","b",100,true),"old network response after track switch");ok(!ApiContract.current("a","a",1600,true),"stale source");ok(!ApiContract.current("a","a",100,false),"disconnected source");ok(!ApiContract.current("a","a",-1,true),"invalid observation time");
  ok(!ApiContract.shouldSeek(1000,800)&&ApiContract.shouldSeek(1000,500),"seek hysteresis");
  JSONObject config=new JSONObject().put("api_version",1).put("maintenance",false).put("features",new JSONObject().put("replacements",true));ApiContract.config(config);boolean blocked=false;try{ApiContract.config(copy(config).put("incident",new JSONObject().put("active",true)));}catch(Exception e){blocked=true;}ok(blocked,"server incident restores original");
  ok(LogStore.secret("password")&&LogStore.secret("refresh_token"),"credential fields redacted");ok(!LogStore.clean("Bearer abc123").contains("abc123"),"bearer redacted");ok(!LogStore.clean("https://x/a?token=private&expires=1").contains("private"),"signed URL redacted");
  System.out.println("PASS: "+tests+" backend, signed URL, expiry, duration, stale response, transport and redaction checks");
 }
}
