package pro.celikom.nativeprobe.identitydiag;
final class LookaheadPrefetchPolicy {
 static final long MIN_LEAD_MS=3000L;
 static final int STABLE_METADATA_SAMPLES=2;
 static boolean metadataComplete(String alias,String title,String artist,String albumId,long durationMs,boolean placeholder){
  return identityMetadataAvailable(alias,title,artist,durationMs)&&albumId!=null&&albumId.matches("\\d{1,15}")&&!placeholder;
 }
 static boolean identityMetadataAvailable(String alias,String title,String artist,long durationMs){
  return alias!=null&&!alias.trim().isEmpty()&&title!=null&&!title.trim().isEmpty()
    &&artist!=null&&!artist.trim().isEmpty()&&durationMs>0;
 }
 static boolean stableMetadataFallbackReady(String alias,String title,String artist,long durationMs,int stableSamples){
  return identityMetadataAvailable(alias,title,artist,durationMs)&&stableSamples>=STABLE_METADATA_SAMPLES;
 }
 static boolean mayResolve(boolean armed,boolean signedIn,boolean sourcePlaying,boolean timelineAvailable,boolean nextDistinct,boolean metadataComplete,long remainingMs){
  return armed&&signedIn&&sourcePlaying&&timelineAvailable&&nextDistinct&&metadataComplete&&remainingMs>=MIN_LEAD_MS;
 }
 static boolean mayPrefetch(boolean armed,boolean signedIn,boolean sourcePlaying,boolean nextItem,boolean uniqueCandidate,long remainingMs){
  return armed&&signedIn&&sourcePlaying&&nextItem&&uniqueCandidate&&remainingMs>=MIN_LEAD_MS;
 }
}
