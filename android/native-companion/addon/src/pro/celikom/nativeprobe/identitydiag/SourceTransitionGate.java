package pro.celikom.nativeprobe.identitydiag;
import java.util.Objects;
/** Never accept an old snapshot across a boundary, and never wait for an alias forever. */
final class SourceTransitionGate {
 static final int ACCEPT=0,WAIT=1,REFRESH=2;static final long MAX_WAIT_MS=1000;
 String expected;long since;boolean pending;
 boolean begin(String next,long now){if(pending&&Objects.equals(expected,next))return false;pending=true;expected=next;since=now;return true;}
 int sample(String actual,long now){if(!pending||expected==null||Objects.equals(expected,actual)){clear();return ACCEPT;}return now-since>=MAX_WAIT_MS?REFRESH:WAIT;}
 void clear(){pending=false;expected=null;since=0;}
}
