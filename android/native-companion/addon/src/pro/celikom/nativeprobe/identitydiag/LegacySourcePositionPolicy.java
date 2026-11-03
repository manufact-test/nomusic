package pro.celikom.nativeprobe.identitydiag;
import java.util.Locale;

/** Bounded, passive agreement gate for a second Yandex session position. */
final class LegacySourcePositionPolicy {
 static final long DIVERGENCE_MS=4000, CONFIRM_MS=250, INITIAL_FRESH_MS=5000, ACTIVE_FRESH_MS=15000;
 static final class Decision {
  final boolean override,newRecovery,failClosed,candidate;
  final long position;
  private Decision(boolean override,boolean newRecovery,boolean failClosed,boolean candidate,long position){
   this.override=override;this.newRecovery=newRecovery;this.failClosed=failClosed;
   this.candidate=candidate;this.position=position;
  }
 }
 static Decision passthrough(){return new Decision(false,false,false,false,-1);}
 static Decision candidate(){return new Decision(false,false,false,true,-1);}
 static Decision unsafe(){return new Decision(false,false,true,false,-1);}
 static Decision recovered(long pos,boolean first){return new Decision(true,first,false,false,pos);}
 private String activeAlias;
 private long disagreementSince=-1;
 private boolean authoritySwitched;
 static String canonical(String s){
  if(s==null)return "";
  return s.trim().replaceAll("\\s+"," ").toLowerCase(Locale.ROOT);
 }
 static boolean sameTrack(String sourceTitle,String sourceArtist,long sourceDuration,
                          String platformTitle,String platformArtist,long platformDuration){
  if(canonical(sourceTitle).isEmpty()||canonical(sourceArtist).isEmpty())return false;
  if(!canonical(sourceTitle).equals(canonical(platformTitle))||
     !canonical(sourceArtist).equals(canonical(platformArtist)))return false;
  return platformDuration<=0||sourceDuration<=0||Math.abs(sourceDuration-platformDuration)<=2000;
 }
 private void song(String alias){
  if(alias!=null&&!alias.equals(activeAlias)){
   activeAlias=alias;disagreementSince=-1;authoritySwitched=false;
  }
 }
 Decision unavailable(String alias){
  song(alias);
  return authoritySwitched?unsafe():passthrough();
 }
 Decision reconcile(String alias,String sourceTitle,String sourceArtist,long duration,
                    long media3Position,boolean media3Playing,
                    String platformTitle,String platformArtist,long platformDuration,
                    long platformPosition,long platformAge,boolean platformPlaying,long now){
  song(alias);
  boolean valid=alias!=null&&media3Position>=0&&media3Position<duration+2000
   &&platformPosition>=0&&platformPosition<=duration+2000
   &&platformAge>=0&&platformAge<=ACTIVE_FRESH_MS
   &&media3Playing&&platformPlaying
   &&sameTrack(sourceTitle,sourceArtist,duration,platformTitle,platformArtist,platformDuration);
  if(!valid){disagreementSince=-1;return authoritySwitched?unsafe():passthrough();}
  long delta=Math.abs(platformPosition-media3Position);
  if(delta<=1000){
   disagreementSince=-1;authoritySwitched=false;
   return passthrough();
  }
  if(delta<DIVERGENCE_MS){
   disagreementSince=-1;
   return authoritySwitched?recovered(platformPosition,false):passthrough();
  }
  if(authoritySwitched)return recovered(platformPosition,false);
  if(platformAge>INITIAL_FRESH_MS){disagreementSince=-1;return passthrough();}
  if(disagreementSince<0){disagreementSince=now;return candidate();}
  if(now-disagreementSince<CONFIRM_MS)return candidate();
  authoritySwitched=true;disagreementSince=-1;
  return recovered(platformPosition,true);
 }
}
