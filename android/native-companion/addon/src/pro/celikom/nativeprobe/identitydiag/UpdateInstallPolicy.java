package pro.celikom.nativeprobe.identitydiag;
/** Pure post-install gate: never clean the task for a canceled or stale session. */
final class UpdateInstallPolicy {
 private UpdateInstallPolicy(){}
 static boolean shouldRemoveRecents(boolean installerSuccess,int expectedCode,int installedCode){
  return installerSuccess&&expectedCode>0&&installedCode==expectedCode;
 }
}
