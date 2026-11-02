package pro.celikom.nativeprobe.identitydiag;
final class LookaheadPrefetchPolicy {
 static final long MIN_LEAD_MS=3000L;
 static boolean metadataComplete(String alias,String title,String artist,String albumId,long durationMs,boolean placeholder){
  return alias!=null&&!alias.trim().isEmpty()&&title!=null&&!title.trim().isEmpty()&&artist!=null&&!artist.trim().isEmpty()&&albumId!=null&&albumId.matches("\\d{1,15}")&&durationMs>0&&!placeholder;
 }
 static boolean mayResolve(boolean armed,boolean signedIn,boolean sourcePlaying,boolean timelineAvailable,boolean nextDistinct,boolean metadataComplete,long remainingMs){
  return armed&&signedIn&&sourcePlaying&&timelineAvailable&&nextDistinct&&metadataComplete&&remainingMs>=MIN_LEAD_MS;
 }
 static boolean mayPrefetch(boolean armed,boolean signedIn,boolean sourcePlaying,boolean nextItem,boolean uniqueCandidate,long remainingMs){
  return armed&&signedIn&&sourcePlaying&&nextItem&&uniqueCandidate&&remainingMs>=MIN_LEAD_MS;
 }
}
