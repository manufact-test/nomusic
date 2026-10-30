package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.media.audiofx.AudioEffect;
import java.util.Objects;
/** Authoritative audio output permission and lifecycle state, confined to service handler. */
final class AudioOwnership {
 enum State { SOURCE_ONLY, PREPARING, ALIGNING, REPLACEMENT, PAUSED, RECOVERING, TRACK_UNSUPPORTED, STOPPED }
 private State state=State.SOURCE_ONLY;
 private String key,reason="initial";
 private long generation=1,pauseEpoch;
 private boolean originalMuted;
 private DynamicsProcessing attachedEffect;
 private float commandedSecondary;
 private MediaPlayer lastVolumePlayer;
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
 /** Retire decoder callbacks even when recovery retries the exact same song.
  * Source gain restoration on a long pause does NOT retire the decoder. */
 void retireDecoder(){generation++;pauseEpoch++;reason="decoder_retired";}
 void preparing(){state=State.PREPARING;reason="preparing";}
 /** Attach the current source effect only after the previous effect has retired. */
 void prepareSourceEffect(DynamicsProcessing candidate){
  if(key==null||state==State.STOPPED||candidate==null||!candidate.hasControl())
   throw new IllegalStateException("unverified source session");
  if(attachedEffect!=null||commandedSecondary>0.001f)
   throw new IllegalStateException("audio effect still owned by previous transition");
  candidate.setInputGainAllChannelsTo(0f);
  if(candidate.setEnabled(true)!=AudioEffect.SUCCESS)
   throw new IllegalStateException("cannot enable original attenuation");
  attachedEffect=candidate;
  preparing();
 }
 void aligning(){state=State.ALIGNING;reason="aligning";}
 void replacement(){if(!originalMuted)throw new IllegalStateException("source not muted");state=State.REPLACEMENT;reason="replacement";}
 void paused(){state=State.PAUSED;reason="paused";pauseEpoch++;}
 long pauseLease(){return pauseEpoch;}
 boolean validPause(long lease){return state==State.PAUSED && pauseEpoch==lease;}
 void cancelPause(){pauseEpoch++;if(state==State.PAUSED){state=State.ALIGNING;reason="resume";}}
 void source(){state=State.SOURCE_ONLY;originalMuted=false;attachedEffect=null;commandedSecondary=0f;lastVolumePlayer=null;pauseEpoch++;reason="source_restored";}
 void recovering(String why){state=State.RECOVERING;pauseEpoch++;reason=why;}
 void unsupported(String why){state=State.TRACK_UNSUPPORTED;pauseEpoch++;reason=why;}
 void stopped(){generation++;pauseEpoch++;key=null;originalMuted=false;attachedEffect=null;commandedSecondary=0f;lastVolumePlayer=null;state=State.STOPPED;reason="stopped";}
 void grantReplacement(DynamicsProcessing effect){
  if(key==null||(state!=State.ALIGNING&&state!=State.REPLACEMENT))throw new IllegalStateException("handover requires current aligning track");
  if(effect==null||effect!=attachedEffect||!effect.hasControl()||!effect.getEnabled())
   throw new IllegalStateException("no verified source attenuation");
  // Avoid repeated DSP writes during stable playback polling.
  if(!originalMuted)effect.setInputGainAllChannelsTo(-100f);
  originalMuted=true;state=State.REPLACEMENT;reason="exclusive_grant";
 }
 /* Fade the original only while the replacement remains silent.
    Grant exclusive replacement only at the final -100 dB step. */
 void fadeSourceBeforeGrant(DynamicsProcessing effect,float progress){
  if(state!=State.ALIGNING||originalMuted||effect==null||effect!=attachedEffect
      ||!effect.hasControl()||!effect.getEnabled()||commandedSecondary>0.001f)
   throw new IllegalStateException("source fade requires silent current replacement");
  if(!Float.isFinite(progress)||progress<0f||progress>1f)
   throw new IllegalArgumentException("invalid source fade progress");
  effect.setInputGainAllChannelsTo(-100f*progress);
 }
 /** No code may send a positive secondary volume without the verified grant. */
 void volume(MediaPlayer player,float value,DynamicsProcessing effect){
  if(player==null)throw new IllegalStateException("no decoder");
  if(!Float.isFinite(value)||value<0f||value>1f)throw new IllegalArgumentException("invalid decoder volume");
  if(value>0.001f && (state!=State.REPLACEMENT || !originalMuted ||
     effect==null || effect!=attachedEffect || !effect.hasControl() || !effect.getEnabled()))
   throw new IllegalStateException("secondary gain without exclusive owner");
  // Always send emergency silence; coalesce only unchanged verified gain.
  if(value<=0.001f||player!=lastVolumePlayer||Float.compare(commandedSecondary,value)!=0)
   player.setVolume(value,value);
  commandedSecondary=value;lastVolumePlayer=player;
 }
 /** Silence or force-release secondary before the caller can restore source gain. */
 void silenceReplacement(MediaPlayer player){
  state=State.RECOVERING;reason="silencing_secondary";
  if(player==null)return;
  boolean muted=false,paused=false;
  try{player.setVolume(0f,0f);commandedSecondary=0f;muted=true;}catch(RuntimeException ignored){}
  try{if(player.isPlaying())player.pause();paused=true;}catch(RuntimeException ignored){}
  if(!muted||!paused)try{player.release();}catch(RuntimeException ignored){}
 }
 /** Only the current source owner can start a decoder. First starts must stay inaudible. */
 void startDecoder(MediaPlayer player,DynamicsProcessing effect,String identity,long ticket){
  if(player==null||!current(ticket,identity))throw new IllegalStateException("stale decoder start");
  if(state!=State.PREPARING&&state!=State.ALIGNING&&state!=State.REPLACEMENT)
   throw new IllegalStateException("decoder start outside active lifecycle");
  if(effect==null||effect!=attachedEffect||!effect.hasControl()||!effect.getEnabled())
   throw new IllegalStateException("cannot start decoder without verified session effect");
  if(commandedSecondary>0.001f&&state!=State.REPLACEMENT)
   throw new IllegalStateException("cannot start audible decoder before exclusive grant");
  player.start();
 }
 /** Pause is always allowed: emergency silencing must not be blocked by a stale token. */
 void pauseDecoder(MediaPlayer player){
  if(player!=null&&player.isPlaying())player.pause();
 }
 /** Every resync and warm seek must be an inaudible command for the current identity. */
 void seekDecoder(MediaPlayer player,long target,String identity,long ticket){
  if(player==null||!current(ticket,identity))throw new IllegalStateException("stale decoder seek");
  if(state!=State.ALIGNING&&state!=State.PAUSED)
   throw new IllegalStateException("seek outside silent alignment");
  if(commandedSecondary>0.001f)throw new IllegalStateException("audible decoder seek forbidden");
  player.seekTo(Math.max(0L,target),MediaPlayer.SEEK_CLOSEST);
 }
 static final class RestoreResult { boolean gainReset,disabled,released; }
 /** Secondary decoder must be silent or released before resetting native gain. */
 RestoreResult restoreSource(MediaPlayer secondary,DynamicsProcessing effect){
  silenceReplacement(secondary);
  RestoreResult r=new RestoreResult();
  if(effect!=null){
   try{effect.setControlStatusListener(null);}catch(RuntimeException ignored){}
   try{effect.setInputGainAllChannelsTo(0f);r.gainReset=true;}catch(RuntimeException ignored){}
   try{r.disabled=effect.setEnabled(false)==AudioEffect.SUCCESS;}catch(RuntimeException ignored){}
   try{effect.release();r.released=true;}catch(RuntimeException ignored){}
  }
  source();return r;
 }
 static boolean exclusive(float original,float secondary){return original<=0.001f||secondary<=0.001f;}
}
