package pro.celikom.nativeprobe.identitydiag;
import java.util.*;
/** Rolling work budget instead of a lifetime song/request ceiling. */
final class RequestBudget {
 static final long WINDOW_MS=12*60*1000L, RETRY_MS=30000;
 long window=-1;int used;final LinkedHashMap<String,Long> recent=new LinkedHashMap<>();
 boolean allow(String id,long now){
  if(window<0||now-window>=WINDOW_MS){window=now;used=0;recent.clear();}
  Long last=recent.get(id);if(used>=24||(last!=null&&now-last<RETRY_MS))return false;
  recent.remove(id);recent.put(id,now);used++;while(recent.size()>128)recent.remove(recent.keySet().iterator().next());return true;
 }
 void clearCooldowns(){recent.clear();}
}
