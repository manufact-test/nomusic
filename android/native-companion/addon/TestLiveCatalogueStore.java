package pro.celikom.nativeprobe.identitydiag;

import org.json.JSONObject;
import java.io.File;
import java.nio.file.Files;

/** The in-app catalogue is replaceable without rebuilding or reinstalling. */
public final class TestLiveCatalogueStore {
 static int checks;
 static void check(boolean yes,String msg){checks++;if(!yes)throw new AssertionError(msg);}
 static JSONObject snapshot(int count,long now)throws Exception{
  JSONObject root=new JSONObject().put("schema",1)
   .put("source","celikom_owner_catalog_snapshot")
   .put("generated_at_ms",now).put("complete",true).put("total_tracks",count);
  org.json.JSONArray rows=new org.json.JSONArray();
  for(int n=0;n<count;n++)rows.put(new JSONObject()
   .put("track_id",String.valueOf(118910020+n))
   .put("title","Мне нужна любовь "+n).put("artist","Татем")
   .put("duration_ms",102380).put("replacement_available",true));
  return root.put("tracks",rows);
 }
 static void invalid(JSONObject root,long now,String reason){
  try{LiveCatalogueStore.validate(root,now);throw new AssertionError("Accepted "+reason);}
  catch(org.json.JSONException expected){checks++;}
 }
 public static void main(String[] args)throws Exception{
  long now=System.currentTimeMillis();
  File dir=Files.createTempDirectory("celikom-live-catalogue").toFile();
  File file=new File(dir,"catalog-live.json");
  JSONObject old=snapshot(1,now),newer=snapshot(2,now+500);
  check(LiveCatalogueStore.load(file,now)==null,"no initial file");
  check(LiveCatalogueStore.save(file,old),"write old");
  check(LiveCatalogueStore.load(file,now).getInt("total_tracks")==1,"reload original");
  check(LiveCatalogueStore.save(file,newer),"replace without APK change");
  check(LiveCatalogueStore.load(file,now+500).getInt("total_tracks")==2,"latest approved song present");
  invalid(snapshot(1,now-8*86400000L),now,"expired catalogue");
  invalid(snapshot(1,now+3600000),now,"future timestamp");
  invalid(snapshot(5001,now),now,"over 5000");
  JSONObject dup=snapshot(2,now);
  dup.getJSONArray("tracks").getJSONObject(1).put("track_id","118910020");
  invalid(dup,now,"duplicate ID");
  JSONObject truncated=snapshot(2,now).put("total_tracks",3);
  invalid(truncated,now,"truncated data");
  JSONObject pending=snapshot(1,now);
  pending.getJSONArray("tracks").getJSONObject(0).put("replacement_available",false);
  invalid(pending,now,"unapproved song");
  JSONObject corrupted=new JSONObject().put("schema",1);
  invalid(corrupted,now,"incomplete root");
  check(file.delete()&&dir.delete(),"cleanup");
  System.out.println("PASS: "+checks+" live catalogue atomic cache and validation checks");
 }
}
