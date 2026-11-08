package pro.celikom.nativeprobe.identitydiag;
import java.util.*;
import org.json.*;

/** Black-box regression using real HybridIdentity approved metadata decisions.
 * Simulates the Test.65 HONOR "ИСКАЛА"/"Гармония" HTTP 451 outcome. */
public final class TestCatalogueNotification {
 static int checks;
 static void ok(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static JSONObject catalogue(long age)throws Exception{
  JSONObject j=new JSONObject().put("schema",1).put("complete",true).put("generated_at_ms",System.currentTimeMillis()-age);
  JSONArray rows=new JSONArray();
  rows.put(new JSONObject().put("track_id","85025192").put("title","Пушка").put("artist","10AGE").put("duration_ms",177000).put("replacement_available",true));
  j.put("tracks",rows);return j;
 }
 static AppPresentation.Input input(Map<String,Object> own,String reason){
  AppPresentation.Input s=new AppPresentation.Input();s.signed=true;s.running=true;s.enabled=true;s.session=true;s.source=true;s.playing=true;s.identityReason=reason;
  s.catalogueFresh=Boolean.TRUE.equals(own.get("catalogueFreshComplete"));
  if(s.catalogueFresh)s.catalogueStatus=String.valueOf(own.get("status"));
  return s;
 }
 static String notice(AppPresentation.Input s){
  return NotificationState.of(s,"ИСКАЛА","Земфира",false,false,false,false).text;
 }
 public static void main(String[] a)throws Exception{
  JSONObject data=catalogue(1000);
  Map<String,Object> none=HybridIdentity.own(data,"ИСКАЛА","Земфира",271000,System.currentTimeMillis());
  ok("NO_MATCH".equals(none.get("status")),"No-matching approved catalogue must be explicit");
  AppPresentation.Input stillWaiting=input(none,"waiting_for_album_response");
  ok(notice(stillWaiting).contains("одобренном каталоге"),"Do not wait for Yandex 451 when local approved absence is already known");
  ok(!notice(stillWaiting).contains("Определяем"),"Never say we are identifying a title already present in notification");
  ok(AppPresentation.of(stillWaiting).showTrack,"Show Yandex song title in activity without Track ID");
  AppPresentation.Input after451=input(none,"album_region_restricted");
  ok(notice(after451).contains("одобренном каталоге"),"451 still cannot hide known catalogue result");
  ok(!NotificationState.of(after451,"ИСКАЛА","Земфира",false,false,false,false).suggest,"No ID never allows suggesting/uploading");
  after451.playing=false;
  ok(notice(after451).contains("Пауза · нет одобренной"),"Paused unknown track retains catalogue outcome");

  Map<String,Object> approved=HybridIdentity.own(data,"Пушка","10AGE",177000,System.currentTimeMillis());
  ok("UNIQUE_METADATA_CANDIDATE".equals(approved.get("status")),"Known approved version must be found");
  AppPresentation.Input matching=input(approved,"waiting_for_album_response");
  ok(notice(matching).contains("Версия есть в каталоге"),"Immediate availability before Yandex finishes album resolution");
  ok(!notice(matching).contains("Определяем"),"Known approved song cannot show undefined progress");

  Map<String,Object> stale=HybridIdentity.own(catalogue(9L*86400000L),"ИСКАЛА","Земфира",271000,System.currentTimeMillis());
  ok(!Boolean.TRUE.equals(stale.get("catalogueFreshComplete")),"Stale snapshot does not prove absence");
  AppPresentation.Input staleInput=input(stale,"waiting_for_album_response");
  ok(notice(staleInput).contains("Проверяем наличие"),"Unknown catalogue only permits an honest check state");
  ok(!notice(staleInput).contains("Определяем песню"),"Progress should refer to checking CELIKOM, not title ID");
  AppPresentation.Input end=input(stale,"album_region_restricted");
  ok(notice(end).contains("статус версии неизвестен"),"When both sources unavailable, do not invent a replacement status");

  AppPresentation.Input missing=input(approved,"unique_album_candidate");missing.identified=true;missing.missing=true;
  ok(notice(missing).contains("нет замены"),"Proven server found=false retains historical notification");
  AppPresentation.Input replacing=input(approved,"unique_album_candidate");replacing.identified=true;replacing.replacing=true;
  ok(notice(replacing).contains("Играет версия CELIKOM"),"Actual replacement remains unchanged");

  System.out.println("PASS: catalogue-first notification status with fresh/stale, pending/451 and replacement, checks="+checks);
 }
}
