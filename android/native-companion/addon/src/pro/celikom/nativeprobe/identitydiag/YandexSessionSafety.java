package pro.celikom.nativeprobe.identitydiag;

/* Conservative, pure policy: a reported session change may stop replacement,
   but never authorizes re-attachment to an unverified source session. */
final class YandexSessionSafety {
 static final String OPEN="android.media.action.OPEN_AUDIO_EFFECT_CONTROL_SESSION";
 static final String CLOSE="android.media.action.CLOSE_AUDIO_EFFECT_CONTROL_SESSION";
 static boolean shouldFailClosed(boolean armed,boolean yandexPackageMatches,String action,int reportedSession,int trustedSession){
  if(!armed||!yandexPackageMatches||reportedSession<=0||trustedSession<=0)return false;
  if(OPEN.equals(action))return reportedSession!=trustedSession;
  if(CLOSE.equals(action))return reportedSession==trustedSession;
  return false;
 }
}
