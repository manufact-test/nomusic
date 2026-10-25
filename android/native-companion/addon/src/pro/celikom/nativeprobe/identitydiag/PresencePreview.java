package pro.celikom.nativeprobe.identitydiag;
import java.util.LinkedHashMap;
/** Five-minute UI preview only. Never returned in place of a fresh contribution/access check. */
final class PresencePreview {
 static final long MAX_AGE_MS=300000;
 static final class Entry {final String status;final long generation,at;Entry(String s,long g,long t){status=s;generation=g;at=t;}}
 final LinkedHashMap<String,Entry> entries=new LinkedHashMap<>();
 synchronized void put(String id,String status,long generation,long now){if(id==null||!("none".equals(status)||"pending".equals(status)||"approved".equals(status)))return;entries.remove(id);entries.put(id,new Entry(status,generation,now));while(entries.size()>32)entries.remove(entries.keySet().iterator().next());}
 synchronized String get(String id,long generation,long now){Entry e=entries.get(id);return e!=null&&e.generation==generation&&now>=e.at&&now-e.at<MAX_AGE_MS?e.status:"";}
 synchronized void clear(){entries.clear();}
}
