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
 /* Measured encoder padding/outro may differ from native timeline.
    Source remains the authoritative transport; never trust an unverified song. */
 static final long MAX_VERIFIED_TAIL_MS=1500;
 static boolean compatible(long sourceMs,long reportedMs,long measuredMs,boolean verifiedIdentity){
  if(!metadataProbeAllowed(sourceMs,reportedMs)||measuredMs<=0||
      Math.abs(reportedMs-measuredMs)>MAX_METADATA_PROBE_DIFFERENCE_MS)return false;
  return safe(sourceMs,measuredMs) ||
      (verifiedIdentity&&Math.abs(sourceMs-measuredMs)<=MAX_VERIFIED_TAIL_MS);
 }
 static boolean boundedTail(long sourceMs,long measuredMs){
  return measuredMs>0&&sourceMs>measuredMs&&
      sourceMs-measuredMs<=MAX_VERIFIED_TAIL_MS;
 }
 static boolean expectedTail(long sourceMs,long measuredMs,long remainingMs){
  return boundedTail(sourceMs,measuredMs)&&remainingMs>=0&&
      remainingMs<=sourceMs-measuredMs+350;
 }
 static boolean safe(long nativeMs,long replacementMs){
  return nativeMs>0&&replacementMs>0&&Math.abs(nativeMs-replacementMs)<=MAX_TAIL_DIFFERENCE_MS;
 }
}
