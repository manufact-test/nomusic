package pro.celikom.nativeprobe.identitydiag;
/** Prevent early completion and late overlap if the replacement differs visibly in length. */
final class PlaybackDuration {
 static final long MAX_TAIL_DIFFERENCE_MS=500;
 /* Metadata may be inaccurate; decoder duration is the final authority.
    The probe bound does not relax audible replacement tolerance. */
 static final long MAX_METADATA_PROBE_DIFFERENCE_MS=1500;
 static boolean metadataProbeAllowed(long nativeMs,long reportedMs){
  return nativeMs>0&&reportedMs>0&&Math.abs(nativeMs-reportedMs)<=MAX_METADATA_PROBE_DIFFERENCE_MS;
 }
 static boolean safe(long nativeMs,long replacementMs){
  return nativeMs>0&&replacementMs>0&&Math.abs(nativeMs-replacementMs)<=MAX_TAIL_DIFFERENCE_MS;
 }
}
