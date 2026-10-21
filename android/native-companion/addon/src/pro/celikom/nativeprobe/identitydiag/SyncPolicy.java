package pro.celikom.nativeprobe.identitydiag;
/** A stable Bluetooth output-clock offset is not a user seek. */
final class SyncPolicy {
 static final long TOLERATED_DRIFT_MS=1500, CONFIRM_MS=1000;
 long excessiveSince=-1;
 boolean correct(boolean aligned,long drift,boolean sourceJump,long now){
  if(!aligned||sourceJump){reset();return true;}
  if(Math.abs(drift)<=TOLERATED_DRIFT_MS){reset();return false;}
  if(excessiveSince<0)excessiveSince=now;
  return now-excessiveSince>=CONFIRM_MS;
 }
 void reset(){excessiveSince=-1;}
}
