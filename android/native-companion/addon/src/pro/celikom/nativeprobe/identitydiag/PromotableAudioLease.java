package pro.celikom.nativeprobe.identitydiag;

import java.util.function.BooleanSupplier;

/**
 * A single verified stream survives a NEXT -> CURRENT ownership handoff.
 * The caller controls the lease; network and MediaPlayer threads only read it.
 * Promotion changes the predicate atomically without closing the stream or
 * invalidating a file that the decoder is already reading.
 */
final class PromotableAudioLease implements BooleanSupplier {
 private volatile BooleanSupplier current;
 private volatile boolean revoked;
 private volatile boolean promoted;

 PromotableAudioLease(BooleanSupplier speculative) {current=speculative;}

 @Override public boolean getAsBoolean() {
  BooleanSupplier predicate=current;
  return !revoked&&predicate!=null&&predicate.getAsBoolean();
 }

 void promote(BooleanSupplier foreground) {
  if(foreground==null)throw new IllegalArgumentException("foreground_lease_required");
  if(revoked)throw new IllegalStateException("audio_lease_revoked");
  current=foreground;
  promoted=true;
 }

 void revoke(){revoked=true;current=null;}
 boolean promoted(){return promoted&&!revoked;}
}
