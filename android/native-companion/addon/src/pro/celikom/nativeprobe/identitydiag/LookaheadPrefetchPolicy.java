package pro.celikom.nativeprobe.identitydiag;
final class LookaheadPrefetchPolicy {
 static final long MIN_LEAD_MS=3000L;
 // HONOR Test.44: still-downloading 4+ minute successor files spent a full
 // 1200ms current-track wait and then had to start a verified sparse stream.
 // Keep the full wait for short files and the frozen non-progressive path;
 // a completed lookahead still uses its existing immediate cache handoff.
 static final long LONG_TRACK_MS=240000L;
 static final long LONG_TRACK_CURRENT_WAIT_MS=400L;
 // A promoted long-track full-file transfer which is still young is unlikely
 // to finish during the existing 400ms grace. Yield 200ms earlier to the
 // *same existing verified sparse* current-track fallback; no DSP changes.
 // Mature transfers retain 400ms so near-complete full-file prefetch still wins.
 static final long EARLY_LONG_TRACK_CURRENT_WAIT_MS=200L;
 static final long EARLY_LONG_TRACK_PREFETCH_MIN_AGE_MS=1800L;
 static final long EARLY_LONG_TRACK_PREFETCH_AGE_MS=2600L;
 // A speculative full-file request intentionally waits for the foreground
 // decoder. If Next promotes that item during the queue grace, waiting for
 // the speculative file would add the entire queue delay plus a handoff
 // timeout before verified sparse preparation can even begin.
 static final long SPECULATIVE_QUEUE_YIELD_MS=1100L;
 static boolean queuedLookaheadMustYieldToCurrent(boolean progressive,String phase,long queuedAtMs,long nowMs){
  return progressive&&"downloading".equals(phase)&&queuedAtMs>=0&&nowMs>=queuedAtMs
    &&nowMs-queuedAtMs<SPECULATIVE_QUEUE_YIELD_MS;
 }
 static long promotedCurrentWaitMs(boolean progressive,long durationMs,String phase){
  if(!progressive)return 10000L;
  return durationMs>=LONG_TRACK_MS&&"downloading".equals(phase)
    ?LONG_TRACK_CURRENT_WAIT_MS:1200L;
 }
 static long promotedCurrentWaitMs(boolean progressive,long durationMs,String phase,long prefetchAgeMs){
  long baseline=promotedCurrentWaitMs(progressive,durationMs,phase);
  return baseline==LONG_TRACK_CURRENT_WAIT_MS&&prefetchAgeMs>=EARLY_LONG_TRACK_PREFETCH_MIN_AGE_MS
    &&prefetchAgeMs<EARLY_LONG_TRACK_PREFETCH_AGE_MS
    ?EARLY_LONG_TRACK_CURRENT_WAIT_MS:baseline;
 }
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
