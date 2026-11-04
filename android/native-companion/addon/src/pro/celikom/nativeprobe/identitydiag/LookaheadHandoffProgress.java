package pro.celikom.nativeprobe.identitydiag;

/**
 * Transfer-local evidence for an already-promoted next-song download.
 * The downloader updates this on its own thread; the playback owner only reads
 * volatile primitives and never receives a mutable audio file or source URL.
 */
final class LookaheadHandoffProgress {
 static final long BASE_WAIT_MS = 1200;
 static final long MAX_PROGRESS_GRACE_MS = 900;
 static final long PROGRESS_FRESH_MS = 350;
 static final long POLL_MS = 100;
 private volatile long bytes;
 private volatile long expected = -1;
 private volatile long firstObservedAtMs = -1;
 private volatile long lastAdvancedAtMs = -1;

 void update(long receivedBytes,long expectedBytes,long nowMs) {
  if(expectedBytes<=0||expectedBytes>AudioTransfer.MAX_BYTES
     ||receivedBytes<0||receivedBytes>expectedBytes||nowMs<0)return;
  if(firstObservedAtMs<0)firstObservedAtMs=nowMs;
  if(receivedBytes>bytes)lastAdvancedAtMs=nowMs;
  bytes=receivedBytes;
  expected=expectedBytes;
 }

 long bytes(){return bytes;}
 long expected(){return expected;}
 long estimatedRemainingMs(long nowMs) {
  long size=expected,received=bytes,first=firstObservedAtMs;
  if(size<=0||received<=0||first<0||nowMs<first)return Long.MAX_VALUE;
  // A stable average through the current transfer is a bounded hint, never
  // evidence that the decoder is prepared or audible.
  return (size-received)*Math.max(100,nowMs-first)/received;
 }
 boolean worthWaiting(long nowMs,long waitStartedAtMs) {
  long waited=nowMs-waitStartedAtMs;
  long size=expected,received=bytes,last=lastAdvancedAtMs;
  if(waited<BASE_WAIT_MS||waited>=BASE_WAIT_MS+MAX_PROGRESS_GRACE_MS
     ||size<1024*1024||received<1024*1024
     ||last<0||nowMs<last||nowMs-last>PROGRESS_FRESH_MS)return false;
  // Never delay a genuinely cold or slow speculative transfer merely because
  // it has delivered one 128 KiB block. Require >60% of a verified full length.
  if(received*100<size*60)return false;
  long remainingBudget=BASE_WAIT_MS+MAX_PROGRESS_GRACE_MS-waited;
  return estimatedRemainingMs(nowMs)<=Math.min(800,remainingBudget+POLL_MS);
 }
}
