package pro.celikom.nativeprobe.identitydiag;

/**
 * Permission-free fallback controls for tracks whose own Yandex UI may fail
 * to publish seek/pause changes to the remote Media3 controller.
 * This DOES NOT intercept the Yandex UI and does not grant replacement audio
 * without the existing signed-in, approved and live-current gates.
 */
final class ProblemTrackTransport {
 static final String TOGGLE="pro.celikom.nativeprobe.identitydiag.problem.TOGGLE";
 static final String BACK="pro.celikom.nativeprobe.identitydiag.problem.BACK";
 static final String FORWARD="pro.celikom.nativeprobe.identitydiag.problem.FORWARD";
 static final String NEXT="pro.celikom.nativeprobe.identitydiag.problem.NEXT";
 static final long STEP_MS=30000L;
 static boolean isAction(String action){
  return TOGGLE.equals(action)||BACK.equals(action)||FORWARD.equals(action)||NEXT.equals(action);
 }
 static boolean isKnownStaleMedia3Track(String id){
  return "42884423".equals(id)||"39949113".equals(id);
 }
 static boolean eligible(String trackId,boolean armed,boolean ready,boolean connected,boolean signedIn){
  return isKnownStaleMedia3Track(trackId)&&armed&&ready&&connected&&signedIn;
 }
 static long target(long position,long duration,boolean forward){
  if(duration<=0||position<0)return -1L;
  long candidate=forward?position+STEP_MS:position-STEP_MS;
  return Math.max(0L,Math.min(Math.max(0L,duration-100L),candidate));
 }
 private ProblemTrackTransport(){}
}
