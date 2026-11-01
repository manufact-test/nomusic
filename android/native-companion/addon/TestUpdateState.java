package pro.celikom.nativeprobe.identitydiag;

import java.util.HashMap;
import java.util.Map;

/** Update discovery persistence and defer semantics; no Android UI or network. */
public final class TestUpdateState {
 static int checks;
 static void check(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
 public static void main(String[] args){
  UpdateState empty=UpdateState.restore(new HashMap<String,Object>(),76);
  check(!empty.hasAvailable(76)&&!empty.isVerifiedLatestFor(76),
      "a fresh install does not claim an update or a verified latest state");
  UpdateState found=empty.successfulCheck(76,77,"{\"versionCode\":77}",1000);
  check(found.hasAvailable(76)&&!found.verifiedLatest&&found.availableCode==77,
      "a successful background or foreground check stores the discovered version");
  UpdateState restored=UpdateState.restore(found.toMap(),76);
  check(restored.hasAvailable(76)&&"{\"versionCode\":77}".equals(restored.availableManifest),
      "the candidate survives a preferences round-trip and app recreation");
  UpdateState deferred=restored.afterLater();
  check(deferred.hasAvailable(76)&&deferred.availableCode==77
      &&deferred.availableManifest.equals(restored.availableManifest),
      "Later dismisses the prompt without deleting the discovered update");
  UpdateState failed=deferred.afterFailedCheck();
  check(failed.hasAvailable(76)&&failed.checkedAt==1000,
      "a failed network check preserves the last verified candidate and timestamp");
  UpdateState installed=UpdateState.restore(failed.toMap(),77);
  check(!installed.hasAvailable(77)&&installed.availableCode==0&&installed.availableManifest==null,
      "an already installed candidate is cleared on the next app launch");
  UpdateState latest=empty.successfulCheck(76,0,null,5000);
  check(latest.isVerifiedLatestFor(76)&&!latest.hasAvailable(76),
      "a successful no-update response is stored as verified latest");
  check(latest.shouldSkipAutomaticCheck(5500,3600000,76),
      "a fresh result avoids an unnecessary automatic request");
  check(!latest.shouldSkipAutomaticCheck(3605001,3600000,76),
      "an expired result is refreshed");
  check(!latest.shouldSkipAutomaticCheck(5500,3600000,77),
      "a result for another installed version is never reused");
  UpdateState invalid=UpdateState.restore(found.toMap(),77);
  check(!invalid.hasAvailable(77),"older/equal candidate cannot be shown after install");
  UpdateState malformed=UpdateState.restore(new HashMap<String,Object>(){{
      put("availableCode",77);put("availableManifest"," ");
  }},76);
  check(!malformed.hasAvailable(76),"empty persisted manifest is rejected");
  System.out.println("PASS: "+checks+" update state persistence, defer and freshness checks");
 }
}
