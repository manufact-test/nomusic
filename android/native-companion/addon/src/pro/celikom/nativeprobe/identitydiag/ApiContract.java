package pro.celikom.nativeprobe.identitydiag;
import org.json.*;
import java.net.*;
import java.util.*;
/** Pure validation shared by the network client and host tests. */
final class ApiContract {
 static final String ORIGIN="https://darkred-camel-588676.hostingersite.com";
 static void config(JSONObject j)throws Exception {
  if(j.optInt("api_version")!=1||j.optBoolean("maintenance",true)||j.optJSONObject("features")==null||!j.getJSONObject("features").optBoolean("replacements",false))throw new Exception("service_unavailable");
  String minimum=j.optString("minimum_extension_version","0.4.0");if(!minimum.matches("[0-9]{1,5}[.][0-9]{1,5}[.][0-9]{1,5}"))throw new Exception("invalid_api_config");String[] parts=minimum.split("[.]");int[] supported={0,4,58};for(int i=0;i<3;i++){int n=Integer.parseInt(parts[i]);if(n>supported[i])throw new Exception("android_client_update_required");if(n<supported[i])break;}
  JSONObject incident=j.optJSONObject("incident");if(incident!=null&&incident.optBoolean("active",false))throw new Exception("service_incident");
 }
 static String audio(JSONObject j,long now)throws Exception {
  long id=integer(j,"replacement_id"),duration=integer(j,"duration_ms"),expires=integer(j,"expires_at");integer(j,"version");
  if(!j.optBoolean("found")||id<=0||duration<=0||duration>86400000||j.optInt("version")<1||expires*1000<=now+1000||expires*1000>now+1800000)throw new Exception("invalid_audio_response");
  double gain=j.optDouble("gain_db",0);if(!Double.isFinite(gain)||gain< -12||gain>12)throw new Exception("invalid_audio_response");
  if(!Arrays.asList("audio/mpeg","audio/mp4","audio/wav","audio/x-wav").contains(j.optString("mime_type","audio/mpeg")))throw new Exception("invalid_audio_response");
  URI base=new URI(ORIGIN),u=base.resolve(j.getString("audio_url"));
  if(!"https".equals(u.getScheme())||!base.getHost().equals(u.getHost())||u.getPort()!=-1||u.getRawUserInfo()!=null||u.getRawFragment()!=null||!u.getRawPath().equals("/api/v1/audio/"+id))throw new Exception("invalid_audio_url");
  Map<String,String> q=new HashMap<>();if(u.getRawQuery()==null)throw new Exception("invalid_audio_url");
  for(String part:u.getRawQuery().split("&",-1)){String[] p=part.split("=",-1);if(p.length!=2||q.put(p[0],p[1])!=null)throw new Exception("invalid_audio_url");}
  if(!q.getOrDefault("token","").matches("[a-f0-9]{64}")||!String.valueOf(expires).equals(q.get("expires"))||q.size()!=(q.containsKey("sid")?3:2)||!Arrays.asList("token","expires","sid").containsAll(q.keySet())||(q.containsKey("sid")&&!q.get("sid").matches("[1-9][0-9]{0,17}")))throw new Exception("invalid_audio_url");return u.toString();
 }
 static long integer(JSONObject j,String k)throws Exception {Object v=j.opt(k);if(!(v instanceof Integer)&&!(v instanceof Long))throw new Exception("invalid_audio_response");return ((Number)v).longValue();}
 static boolean durations(long source,long replacement,long measured){return source>0&&replacement>0&&measured>0&&Math.abs(source-replacement)<=5000&&Math.abs(replacement-measured)<=1500;}
 static boolean current(String requested,String current,long age,boolean connected){return requested!=null&&requested.equals(current)&&age>=0&&age<=1500&&connected;}
 static boolean shouldSeek(long source,long replacement){return Math.abs(source-replacement)>350;}
}
