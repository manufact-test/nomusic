package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import java.util.Objects;
/** Authoritative audio output permission and lifecycle state, confined to service handler. */
final class AudioOwnership {
 enum State { SOURCE_ONLY, PREPARING, ALIGNING, REPLACEMENT, PAUSED, RECOVERING, TRACK_UNSUPPORTED, STOPPED }
 private State state=State.SOURCE_ONLY;
 private String key,reason="initial";
 private long generation=1,pauseEpoch;
 private boolean originalMuted;
 State state(){return state;}
 String reason(){return reason;}
 long epoch(){return generation;}
 boolean current(long ticket,String requested){
  return ticket==generation && requested!=null && Objects.equals(key,requested) && state!=State.STOPPED;
 }
 void track(String next){
  if(Objects.equals(key,next))return;
  if(originalMuted)throw new IllegalStateException("track cannot change before secondary silence and source restore");
  generation++;pauseEpoch++;key=next;
  if(state!=State.STOPPED)state=State.SOURCE_ONLY;
  reason="track_changed";
 }
 void activate(){if(state==State.STOPPED){state=State.SOURCE_ONLY;reason="armed";}}

 void invalidate(String why){
  if(originalMuted)throw new IllegalStateException("boundary cannot discard active output lease");
  generation++;pauseEpoch++;key=null;
  if(state!=State.STOPPED)state=State.SOURCE_ONLY;
  reason=why;
 }
 void preparing(){state=State.PREPARING;reason="preparing";}
 void aligning(){state=State.ALIGNING;reason="aligning";}
 void replacement(){if(!originalMuted)throw new IllegalStateException("source not muted");state=State.REPLACEMENT;reason="replacement";}
 void paused(){state=State.PAUSED;reason="paused";pauseEpoch++;}
 long pauseLease(){return pauseEpoch;}
 boolean validPause(long lease){return state==State.PAUSED && pauseEpoch==lease;}
 void cancelPause(){pauseEpoch++;if(state==State.PAUSED){state=State.ALIGNING;reason="resume";}}
 void source(){state=State.SOURCE_ONLY;originalMuted=false;pauseEpoch++;reason="source_restored";}
 void recovering(String why){state=State.RECOVERING;pauseEpoch++;reason=why;}
 void unsupported(String why){state=State.TRACK_UNSUPPORTED;pauseEpoch++;reason=why;}
 void stopped(){generation++;pauseEpoch++;key=null;originalMuted=false;state=State.STOPPED;reason="stopped";}
 void grantReplacement(DynamicsProcessing effect){
  if(key==null||(state!=State.ALIGNING&&state!=State.REPLACEMENT))throw new IllegalStateException("handover requires current aligning track");
  if(effect==null||!effect.hasControl()||!effect.getEnabled())
   throw new IllegalStateException("no verified source attenuation");
  effect.setInputGainAllChannelsTo(-100f);
  originalMuted=true;state=State.REPLACEMENT;reason="exclusive_grant";
 }
 /** No code may send a positive secondary volume without the verified grant. */
 void volume(MediaPlayer player,float value,DynamicsProcessing effect){
  if(player==null)throw new IllegalStateException("no decoder");
  if(!Float.isFinite(value)||value<0f||value>1f)throw new IllegalArgumentException("invalid decoder volume");
  if(value>0.001f && (state!=State.REPLACEMENT || !originalMuted ||
     effect==null || !effect.hasControl() || !effect.getEnabled()))
   throw new IllegalStateException("secondary gain without exclusive owner");
  player.setVolume(value,value);
 }
 /** Silence or force-release secondary before the caller can restore source gain. */
 void silenceReplacement(MediaPlayer player){
  state=State.RECOVERING;reason="silencing_secondary";
  if(player==null)return;
  boolean muted=false,paused=false;
  try{player.setVolume(0f,0f);muted=true;}catch(RuntimeException ignored){}
  try{if(player.isPlaying())player.pause();paused=true;}catch(RuntimeException ignored){}
  if(!muted||!paused)try{player.release();}catch(RuntimeException ignored){}
 }
 static boolean exclusive(float original,float secondary){return original<=0.001f||secondary<=0.001f;}
}
