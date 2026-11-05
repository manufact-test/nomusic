package pro.celikom.nativeprobe.identitydiag;
import java.util.*;
/** Pace requests without a session/window song ceiling. Accessed on the service thread. */
final class RequestBudget {
 static final long MIN_INTERVAL_MS=1500, RETRY_MS=30000;
 // Current track can preempt speculative metadata after 250 ms, preserving same-album cooldown.
 static final long FOREGROUND_AFTER_LOOKAHEAD_MS=250;
 long lastRequest=-1;boolean lastWasLookahead;final LinkedHashMap<String,Long> recent=new LinkedHashMap<>();
 boolean allow(String id,long now){return allow(id,now,true);}
 boolean allow(String id,long now,boolean current){
  Long last=recent.get(id);
  long requiredGap=current&&lastWasLookahead?FOREGROUND_AFTER_LOOKAHEAD_MS:MIN_INTERVAL_MS;
  if((lastRequest>=0&&now-lastRequest<requiredGap)||(last!=null&&now-last<RETRY_MS))return false;
  recent.remove(id);recent.put(id,now);lastRequest=now;lastWasLookahead=!current;
  while(recent.size()>128)recent.remove(recent.keySet().iterator().next());return true;
 }
 void clearCooldowns(){recent.clear();}
}
