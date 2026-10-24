package pro.celikom.nativeprobe.identitydiag;
/** Decoder read-ahead is not proof that audible playback has stalled. */
final class BufferRecoveryGate {
 long checkedAt=-1,lastPosition;static final long NO_PROGRESS_MS=500;
 boolean recover(boolean waiting,boolean playing,boolean seeking,long position,long now){
  if(!waiting||!playing||seeking){reset();return false;}
  if(checkedAt<0||Math.abs(position-lastPosition)>30){checkedAt=now;lastPosition=position;return false;}
  return now-checkedAt>=NO_PROGRESS_MS;
 }
 void reset(){checkedAt=-1;}
}
