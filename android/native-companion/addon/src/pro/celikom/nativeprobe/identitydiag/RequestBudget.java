package pro.celikom.nativeprobe.identitydiag;
import java.util.*;
/** Pace requests without a session/window song ceiling. Accessed on the service thread. */
final class RequestBudget {
 static final long MIN_INTERVAL_MS=1500, RETRY_MS=30000;
 long lastRequest=-1;final LinkedHashMap<String,Long> recent=new LinkedHashMap<>();
 boolean allow(String id,long now){
  Long last=recent.get(id);
  if((lastRequest>=0&&now-lastRequest<MIN_INTERVAL_MS)||(last!=null&&now-last<RETRY_MS))return false;
  recent.remove(id);recent.put(id,now);lastRequest=now;while(recent.size()>128)recent.remove(recent.keySet().iterator().next());return true;
 }
 void clearCooldowns(){recent.clear();}
}
