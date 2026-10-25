package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/** Re-read a quiet buffering controller; never infer playback or issue transport commands. */
final class SourceStateWatchdog {
 static final long BUFFERING_MS=3000, REFRESH_INTERVAL_MS=30000;
 String key;long quietSince=-1,lastRefresh=-1;int state=-1;
 boolean refresh(String nextKey,int nextState,boolean playing,long eventAge,long now){
  if(playing||nextKey==null||nextState!=2){reset();return false;}
  if(!Objects.equals(key,nextKey)||state!=nextState||quietSince<0){key=nextKey;state=nextState;quietSince=now;}
  long wait=BUFFERING_MS;
  if(now-quietSince<wait||eventAge<wait||(lastRefresh>=0&&now-lastRefresh<REFRESH_INTERVAL_MS))return false;
  lastRefresh=now;quietSince=now;return true;
 }
 void reset(){key=null;state=-1;quietSince=-1;}
}
