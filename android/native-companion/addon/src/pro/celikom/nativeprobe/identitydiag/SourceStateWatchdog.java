package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/** Throttled diagnostic for a quiet buffering source; never requests controller release. */
final class SourceStateWatchdog {
 static final long BUFFERING_MS=3000, OBSERVATION_INTERVAL_MS=30000;
 String key;long quietSince=-1,lastObservation=-1;int state=-1;
 boolean observeQuietBuffering(String nextKey,int nextState,boolean playing,long eventAge,long now){
  if(playing||nextKey==null||nextState!=2){reset();return false;}
  if(!Objects.equals(key,nextKey)||state!=nextState||quietSince<0){key=nextKey;state=nextState;quietSince=now;}
  if(now-quietSince<BUFFERING_MS||eventAge<BUFFERING_MS
    ||(lastObservation>=0&&now-lastObservation<OBSERVATION_INTERVAL_MS))return false;
  lastObservation=now;quietSince=now;return true;
 }
 void reset(){key=null;state=-1;quietSince=-1;}
}
