package pro.celikom.nativeprobe.identitydiag;
public final class TestLookaheadPrefetchPolicy {
 static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
 public static void main(String[] a){
  check(LookaheadPrefetchPolicy.metadataComplete("n","T","A","123",180000,false),"complete");
  check(!LookaheadPrefetchPolicy.metadataComplete("","T","A","123",180000,false),"empty alias rejected");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T","A","123",180000,true),"placeholder");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T","A",null,180000,false),"album missing");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T","A","abc",180000,false),"album invalid");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T","A","123",-1,false),"duration missing");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","","A","123",180000,false),"title missing");
  check(!LookaheadPrefetchPolicy.metadataComplete("n","T"," ","123",180000,false),"artist missing");
  check(LookaheadPrefetchPolicy.mayResolve(true,true,true,true,true,true,9000),"resolve");
  check(!LookaheadPrefetchPolicy.mayResolve(false,true,true,true,true,true,9000),"disarmed");
  check(!LookaheadPrefetchPolicy.mayResolve(true,false,true,true,true,true,9000),"signed out");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,false,true,true,true,9000),"paused");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,true,false,true,true,9000),"no timeline");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,true,true,false,true,9000),"not distinct");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,true,true,true,false,9000),"metadata incomplete");
  check(LookaheadPrefetchPolicy.mayResolve(true,true,true,true,true,true,3000),"minimum lead accepted");
  check(!LookaheadPrefetchPolicy.mayResolve(true,true,true,true,true,true,2999),"too late");
  check(LookaheadPrefetchPolicy.mayPrefetch(true,true,true,true,true,9000),"prefetch");
  check(!LookaheadPrefetchPolicy.mayPrefetch(true,true,true,true,false,9000),"ambiguous");
  check(!LookaheadPrefetchPolicy.mayPrefetch(true,true,true,false,true,9000),"stale");
  check(LookaheadPrefetchPolicy.mayPrefetch(true,true,true,true,true,3000),"minimum prefetch lead accepted");
  check(!LookaheadPrefetchPolicy.mayPrefetch(true,true,true,true,true,2999),"too late");
  System.out.println("PASS: lookahead metadata and fail-closed prefetch gates");
 }
}
