package pro.celikom.nativeprobe.identitydiag;
import org.json.*;
import java.util.*;
public final class TestLookaheadPrefetchPolicy {
 static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
 static void metadataOnlyFallbackIsUniqueAndFailClosed()throws Exception{
  JSONArray rows=new JSONArray();
  rows.put(new JSONObject().put("track_id","12345").put("replacement_available",true)
    .put("title","Трек").put("artist","Артист").put("duration_ms",180000));
  JSONObject fresh=new JSONObject().put("schema",1).put("complete",true)
    .put("generated_at_ms",1000).put("tracks",rows);
  Map<String,Object> own=HybridIdentity.own(fresh,"Трек","Артист",180000,2000);
  Map<String,Object> learned=HybridIdentity.metadata("Трек","Артист",180000,Collections.emptyList());
  Map<String,Object> decision=HybridIdentity.decide(null,own,learned,false);
  check("12345".equals(decision.get("candidateTrackId")),
    "fresh unique local metadata may nominate a next-track candidate without album ID");
  rows.put(new JSONObject().put("track_id","12346").put("replacement_available",true)
    .put("title","Трек").put("artist","Артист").put("duration_ms",180000));
  Map<String,Object> ambiguousOwn=HybridIdentity.own(fresh,"Трек","Артист",180000,2000);
  Map<String,Object> ambiguous=HybridIdentity.decide(null,ambiguousOwn,learned,false);
  check(ambiguous.get("candidateTrackId")==null,
    "ambiguous local metadata never authorizes a prefetch candidate");
  JSONObject stale=new JSONObject().put("schema",1).put("complete",true)
    .put("generated_at_ms",1).put("tracks",new JSONArray().put(
      new JSONObject().put("track_id","12345").put("replacement_available",true)
        .put("title","Трек").put("artist","Артист").put("duration_ms",180000)));
  Map<String,Object> staleOwn=HybridIdentity.own(stale,"Трек","Артист",180000,1000000000L);
  List<Map<String,Object>> learnedRows=Arrays.asList(LogStore.map(
    "catalogueTrackId","67890","displayTitle","Трек","artist","Артист","durationMs",180000));
  Map<String,Object> learnedUnique=HybridIdentity.metadata("Трек","Артист",180000,learnedRows);
  Map<String,Object> learnedDecision=HybridIdentity.decide(null,staleOwn,learnedUnique,false);
  check("67890".equals(learnedDecision.get("candidateTrackId")),
    "a stale local snapshot cannot win, but a unique previously fetched album row may be used");
  Map<String,Object> albumAmbiguous=HybridIdentity.decide(
    LogStore.map("status","AMBIGUOUS"),own,learned,false);
  check(albumAmbiguous.get("candidateTrackId")==null,
    "ambiguous album evidence withholds weaker metadata fallback");
 }
 public static void main(String[] a)throws Exception{
  check(LookaheadPrefetchPolicy.metadataComplete("n","T","A","123",180000,false),"complete");
  check(!LookaheadPrefetchPolicy.metadataComplete("","T","A","123",180000,false),"empty alias rejected");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T","A","123",180000,true),"placeholder remains strict unless stable fallback is separately proven");
  check(LookaheadPrefetchPolicy.identityMetadataAvailable("n","T","A",180000),"identity fields without album are available");
  check(!LookaheadPrefetchPolicy.stableMetadataFallbackReady("n","T","A",180000,1),"one metadata sample is not enough");
  check(LookaheadPrefetchPolicy.stableMetadataFallbackReady("n","T","A",180000,2),"two stable metadata samples authorize fallback matching");
  check(!LookaheadPrefetchPolicy.stableMetadataFallbackReady("n","T","A",0,3),"duration is mandatory for metadata fallback");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T","A",null,180000,false),"album missing");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T","A","abc",180000,false),"album invalid");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T","A","123",-1,false),"duration missing");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","","A","123",180000,false),"title missing");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T"," ","123",180000,false),"artist missing");
  check(LookaheadPrefetchPolicy.mayResolve(true,true,true,true,true,true,9000),"resolve");
  check(!LookaheadPrefetchPolicy.mayResolve(false,true,true,true,true,true,9000),"disarmed");
  check(!LookaheadPrefetchPolicy.mayResolve(true,false,true,true,true,true,9000),"signed out");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,false,true,true,true,9000),"paused");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,true,false,true,true,9000),"no timeline");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,true,true,false,true,9000),"not distinct");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,true,true,true,false,9000),"metadata incomplete");
  check(LookaheadPrefetchPolicy.mayResolve(true,true,true,true,true,true,3000),"minimum lead accepted");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,true,true,true,true,2999),"too late");
  check(LookaheadPrefetchPolicy.mayPrefetch(true,true,true,true,true,9000),"prefetch");
  check(!LookaheadPrefetchPolicy.mayPrefetch(true,true,true,true,false,9000),"ambiguous");
  check(!LookaheadPrefetchPolicy.mayPrefetch(true,true,true,false,true,9000),"stale");
  check(LookaheadPrefetchPolicy.mayPrefetch(true,true,true,true,true,3000),"minimum prefetch lead accepted");
  check(!LookaheadPrefetchPolicy.mayPrefetch(true,true,true,true,true,2999),"too late");
  check(LookaheadPrefetchPolicy.queuedLookaheadMustYieldToCurrent(true,"downloading",2000,2500),
    "rapid manual Next bypasses a full-file download that is still in its queue grace");
  check(!LookaheadPrefetchPolicy.queuedLookaheadMustYieldToCurrent(true,"downloading",2000,3100),
    "started speculative transfer retains existing bounded handoff");
  check(!LookaheadPrefetchPolicy.queuedLookaheadMustYieldToCurrent(false,"downloading",2000,2500),
    "frozen nonprogressive path is unchanged");
  check(!LookaheadPrefetchPolicy.queuedLookaheadMustYieldToCurrent(true,"cached",2000,2500),
    "complete cached lookahead is not cancelled");
  // HONOR Test.66: early fallback only for young long-track lookahead.
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,246810,"downloading",2300)==200L,
    "young long-track full download yields earlier to current verified sparse");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,242000,"downloading",3300)==400L,
    "nearly finished lookahead retains 400ms grace");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,240000,"downloading",2599)==200L,
    "early age boundary");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,240000,"downloading",2600)==400L,
    "mature age boundary");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,232450,"downloading",100)==1200L,
    "short track keeps baseline");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(false,246810,"downloading",100)==10000L,
    "frozen nonprogressive unchanged");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,246810,"cached",100)==1200L,
    "cached file unchanged");
  check(LookaheadPrefetchPolicy.promotedCurrentWaitMs(true,246810,"downloading",-1)==400L,
    "unknown age preserves original grace");
  metadataOnlyFallbackIsUniqueAndFailClosed();
  System.out.println("PASS: lookahead strict album and stable metadata fallback gates");
 }
}
