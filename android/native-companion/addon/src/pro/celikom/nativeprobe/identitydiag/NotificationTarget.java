package pro.celikom.nativeprobe.identitydiag;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
/** Immutable activity-action identity, unique per run, song and account. */
final class NotificationTarget {
 static final String ACTION="pro.celikom.nativeprobe.SUGGEST_CURRENT_SONG";
 final String run,id,key;final long account;
 NotificationTarget(String run,String id,String key,long account){this.run=run;this.id=id;this.key=key;this.account=account;}
 boolean matches(String liveRun,String liveId,String liveKey,long liveAccount){return run!=null&&id!=null&&key!=null&&run.equals(liveRun)&&id.equals(liveId)&&key.equals(liveKey)&&account==liveAccount;}
 String fingerprint(){try{byte[] digest=MessageDigest.getInstance("SHA-256").digest((run+"\u0000"+account+"\u0000"+id+"\u0000"+key).getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte value:digest)out.append(String.format(java.util.Locale.ROOT,"%02x",value&255));return out.toString();}catch(Exception e){throw new IllegalStateException(e);}}
}
