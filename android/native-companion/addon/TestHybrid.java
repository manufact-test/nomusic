package pro.celikom.nativeprobe.identitydiag;
import org.json.*;import java.util.*;import java.io.*;
public class TestHybrid {
 static void check(boolean x,String s){if(!x)throw new AssertionError(s);}
 public static void main(String[] args)throws Exception{
  long now=System.currentTimeMillis();JSONObject own=new JSONObject("{\"schema\":1,\"complete\":true,\"tracks\":[{\"track_id\":\"123\",\"title\":\"Песня\",\"artist\":\"А, Б\",\"album\":\"\",\"duration_ms\":120000,\"replacement_available\":true}]}").put("generated_at_ms",now);
  Map<String,Object> fresh=HybridIdentity.own(own,"Песня","Б, А",120000,now),none=LogStore.map("status","NO_MATCH");
  check("UNIQUE_METADATA_CANDIDATE".equals(fresh.get("status")),"own fallback without album and reordered artists");
  check("OWN_CATALOGUE_METADATA".equals(HybridIdentity.decide(null,fresh,none,false).get("method")),"own fallback selected");
  check("NONE".equals(HybridIdentity.decide(null,fresh,none,true).get("method")),"pending primary prevents premature fallback");
  Map<String,Object> stale=HybridIdentity.own(own,"Песня","А, Б",120000,now+8*86400000L);
  Map<String,Object> historical=HybridIdentity.decide(null,stale,none,false);check("OWN_CATALOGUE_HINT".equals(historical.get("method"))&&Boolean.FALSE.equals(historical.get("playbackAuthorized")),"old complete catalogue supplies a hint but never playback authorization");
  Map<String,Object> primary=LogStore.map("status","UNIQUE_CANDIDATE","catalogueTrackId","456");Map<String,Object> decision=HybridIdentity.decide(primary,fresh,none,false);
  check("456".equals(decision.get("candidateTrackId"))&&Boolean.TRUE.equals(decision.get("editionConflict")),"different editions reported explicitly, stronger candidate retained");
  check("NONE".equals(HybridIdentity.decide(LogStore.map("status","AMBIGUOUS"),fresh,none,false).get("method")),"ambiguity cannot be hidden by weaker candidate");
  Map<String,Object> missing=HybridIdentity.own(own,"Песня","А, Б",0,now);check("NONE".equals(HybridIdentity.decide(null,missing,none,false).get("method")),"missing duration never selected");
  List<Map<String,Object>> learned=Arrays.asList(LogStore.map("catalogueTrackId","789","displayTitle","Песня","artist","А, Б","durationMs",120000));
  Map<String,Object> learnedMatch=HybridIdentity.metadata("Песня","Б, А",120000,learned);check("LEARNED_METADATA".equals(HybridIdentity.decide(null,none,learnedMatch,false).get("method")),"learned cache fallback");
  File dir=java.nio.file.Files.createTempDirectory("celikom-identity-test").toFile(),file=new File(dir,"albums.json");new IdentityCache(file).save("42",learned);Map<String,List<Map<String,Object>>> loaded=new IdentityCache(file).load();check(loaded.containsKey("42")&&"789".equals(loaded.get("42").get(0).get("catalogueTrackId")),"persistent cache survives a new instance");file.delete();dir.delete();
  check(Boolean.FALSE.equals(decision.get("playbackAuthorized"))&&Boolean.FALSE.equals(decision.get("replacementStarted")),"diagnostic candidate does not grant playback authorization");
  System.out.println("PASS: hybrid precedence, own catalogue, artist order, stale data, ambiguity, conflicts, missing duration, persistent offline cache, no playback authorization");
 }
}
