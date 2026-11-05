package pro.celikom.nativeprobe.identitydiag;

/** Replay the Test.37 HONOR stale-Media3 incident as a pure safety decision. */
public final class Test38SourceSessionRecheck {
 static int assertions;
 static void check(boolean good,String why){assertions++;if(!good)throw new AssertionError(why);}

 static void incident() {
  SourceSessionRecheck guard=new SourceSessionRecheck();
  check(!guard.trigger(true,true,"255",35000,225,225,800,20652),
      "normal Media3 callback cadence must not reset the source");
  check(!guard.trigger(true,true,"255",35000,300,225,20000,20652),
      "untrusted different session is never authoritative");
  check(!guard.trigger(false,true,"255",35000,225,225,20000,20652),
      "no active replacement must not disturb original playback");
  check(!guard.trigger(true,false,"255",35000,225,225,20000,20652),
      "no connected controller cannot be rechecked");
  check(guard.trigger(true,true,"255",35000,225,225,20614,20652),
      "HONOR report: reopened source session without any Media3 event forces fail-open");
  check(guard.awaitingFreshSource,"old Media3 identity quarantined");
  check(!guard.accept("255",35100,20752),"same old identity and cursor cannot renew audio");
  check(!guard.accept("255",40100,25752),"a merely ticking stale cursor cannot renew audio");
  check(!guard.trigger(true,true,"255",40000,225,225,25000,25752),
      "duplicate source reopen cannot loop reconnect");
  check(guard.accept("256",0,26000),"fresh different song releases quarantine");
  check(!guard.awaitingFreshSource,"new item clears stale fence");
  check(!guard.trigger(true,true,"256",100,225,225,25000,26000),
      "cooldown protects against rapid repeated audio-effect OPEN signals");
  check(guard.trigger(true,true,"256",12000,225,225,20000,35645),
      "subsequent independent, quiet source session may be rechecked");
  check(guard.accept("256",30000,35700),"new seek position from fresh controller is evidence");
 }

 static void events() {
  SourceSessionRecheck guard=new SourceSessionRecheck();
  check(guard.trigger(true,true,"255",51000,225,225,10000,60000),"begin quarantine");
  check(!guard.confirmFreshSeek("255",200,50500),"old controller cursor must not release fence");
  check(!guard.confirmFreshSeek("256",200,200),"unrelated alias must not prove seek");
  check(guard.confirmFreshSeek("255",30000,30080),"verified fresh seek event releases quarantine");
  check(!guard.awaitingFreshSource,"seek cleared stale fence");
  check(guard.accept(null,-1,61000),"outside quarantine regular unavailable policy remains in charge");
 }

 public static void main(String[]args){incident();events();
  System.out.println("PASS: "+assertions+" Test.38 source-controller fail-open/recheck assertions");}
}
