package pro.celikom.nativeprobe.identitydiag;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
/** Local support-export policy. Identity must come from a fresh authenticated auth/me response. */
final class DiagnosticAccess {
 static boolean user(JSONObject response){
  JSONObject u=response==null?null:response.optJSONObject("user");
  if(u==null||u.optLong("id",0)<=0||!"active".equals(u.optString("status")))return false;
  try{byte[] bytes=MessageDigest.getInstance("SHA-256").digest(u.optString("email","").trim().toLowerCase(Locale.ROOT).getBytes(StandardCharsets.UTF_8));StringBuilder h=new StringBuilder();for(byte b:bytes)h.append(String.format(Locale.ROOT,"%02x",b&255));return digest(h.toString());}catch(Exception e){return false;}
 }
 static boolean lease(boolean signed,long grant,long account,long now,long until){return signed&&grant==account&&now<until;}
 static boolean digest(String h){return "18e9af33bc55e691582e0495d6f9024611649a3342742ec7569cd565e28af572".equals(h)||"50bc7e488885f21b0af751f8e2ed3bc622d3bc097c6541817c9ef742cdf7777e".equals(h);}
}
