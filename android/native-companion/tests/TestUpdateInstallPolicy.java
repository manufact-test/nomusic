package pro.celikom.nativeprobe.identitydiag;
/** Status callback never clears the task before a verified package update. */
public final class TestUpdateInstallPolicy {
 public static void main(String[] args){
  if(!UpdateInstallPolicy.shouldRemoveRecents(true,71,71))throw new AssertionError("confirmed update should remove task");
  if(UpdateInstallPolicy.shouldRemoveRecents(false,71,71))throw new AssertionError("pending/failed install removes task");
  if(UpdateInstallPolicy.shouldRemoveRecents(true,71,70))throw new AssertionError("stale installed version removes task");
  if(UpdateInstallPolicy.shouldRemoveRecents(true,-1,71))throw new AssertionError("missing expected code removes task");
  if(UpdateInstallPolicy.shouldRemoveRecents(true,70,71))throw new AssertionError("other install removes task");
  System.out.println("PASS: post-install task cleanup requires confirmed version match");
 }
}
