package pro.celikom.nativeprobe.identitydiag;
/** Prevent early completion and late overlap if the replacement differs visibly in length. */
final class PlaybackDuration {
 static final long MAX_TAIL_DIFFERENCE_MS=500;
 static boolean safe(long nativeMs,long replacementMs){
  return nativeMs>0&&replacementMs>0&&Math.abs(nativeMs-replacementMs)<=MAX_TAIL_DIFFERENCE_MS;
 }
}
