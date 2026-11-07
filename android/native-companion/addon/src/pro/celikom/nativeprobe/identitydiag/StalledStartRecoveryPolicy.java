package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/** Single, same-controller recovery attempt only for a source stuck at the
 * START of an identified item. Never touches healthy transitions or seeks. */
final class StalledStartRecoveryPolicy {
 static final long STALL_MS=4200, MIN_EVENT_AGE_MS=3500, MAX_START_POSITION_MS=500;
 String alias;long bufferingSince=-1;boolean attempted;
 boolean shouldRecover(String nextAlias,boolean buffering,boolean wantsToPlay,
  boolean playing,long position,long ageOfLastMediaEvent,long now){
  if(nextAlias==null||nextAlias.isEmpty()) {clear();return false;}
  if(!Objects.equals(nextAlias,alias)){alias=nextAlias;bufferingSince=-1;attempted=false;}
  if(!buffering||!wantsToPlay||playing||position<0||position>MAX_START_POSITION_MS){
   bufferingSince=-1;return false;
  }
  if(bufferingSince<0)bufferingSince=now;
  if(attempted||now-bufferingSince<STALL_MS||ageOfLastMediaEvent<MIN_EVENT_AGE_MS)return false;
  attempted=true;return true;
 }
 void clear(){alias=null;bufferingSince=-1;attempted=false;}
}
