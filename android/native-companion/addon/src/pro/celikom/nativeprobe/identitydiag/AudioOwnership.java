package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.media.audiofx.AudioEffect;
import java.util.Objects;
/** Authoritative audio output permission and lifecycle state, confined to service handler. */
final class AudioOwnership {
 enum State { SOURCE_ONLY, PREPARING, ALIGNING, REPLACEMENT, PAUSED, RECOVERING, TRACK_UNSUPPORTED, STOPPED }
 /* Event and ticket authority lives with the sole audio output owner. A data ticket
    survives an ordinary seek/pause, but never a source/account/edition change. */
 enum Event { PREPARE, PREPARE_READY, SEEK, BUFFERING, PAUSE, RESUME, HANDOVER, BOUNDARY, ROUTE_LOSS, LOGOUT, STOP }
 static final class Ticket {
  final String sourceKey;
  final long sourceEpoch,operationEpoch,accountEpoch,replacementId,version,durationMs;
  Ticket(String key,long source,long operation,long account,long replacement,long version,long duration){
   sourceKey=key;sourceEpoch=source;operationEpoch=operation;accountEpoch=account;
   replacementId=replacement;this.version=version;durationMs=duration;
  }
 }
 private long operationEpoch=1;
 /* Native seek completions are untagged. Only one seek is issued per decoder
    until its callback is consumed; old work cannot masquerade as a new seek. */
 enum SeekKind { ALIGNMENT, WARM }
 static final class SeekAck {
  final SeekKind kind;final long operationEpoch,submittedAt;
  SeekAck(SeekKind k,long epoch,long at){kind=k;operationEpoch=epoch;submittedAt=at;}
 }
 private MediaPlayer inFlightDecoder;
 private SeekKind inFlightKind;
 private long inFlightEpoch,inFlightAt;
 boolean seekInFlight(MediaPlayer p){return p!=null&&p==inFlightDecoder;}
 boolean seekExpired(MediaPlayer p,long now,long budget){return seekInFlight(p)&&now-inFlightAt>budget;}
 private void clearSeekFlight(){inFlightDecoder=null;inFlightKind=null;inFlightEpoch=0;inFlightAt=0;}
 boolean issueSeek(MediaPlayer p,long target,String key,long ticket,SeekKind kind,long now){
  if(inFlightDecoder!=null)return false;
  if(kind==null)throw new IllegalArgumentException("seek kind required");
  inFlightDecoder=p;inFlightKind=kind;inFlightEpoch=operationEpoch;inFlightAt=now;
  try{seekDecoder(p,target,key,ticket);}catch(RuntimeException e){clearSeekFlight();throw e;}
  return true;
 }
 SeekAck acceptSeekCompletion(MediaPlayer p){
  if(p==null||p!=inFlightDecoder)return null;
  SeekAck ack=new SeekAck(inFlightKind,inFlightEpoch,inFlightAt);
  clearSeekFlight();return ack;
 }
 long operationEpoch(){return operationEpoch;}
 Ticket ticket(String key,long account,long replacement,long version,long duration){
  if(!current(generation,key))throw new IllegalStateException("ticket without current source");
  return new Ticket(key,generation,operationEpoch,account,replacement,version,duration);
 }
 boolean dataCurrent(Ticket t,long account,String key,long replacement,long version,long duration){
  return t!=null&&current(t.sourceEpoch,t.sourceKey)&&Objects.equals(t.sourceKey,key)
    &&t.accountEpoch==account&&t.replacementId==replacement&&t.version==version&&t.durationMs==duration;
 }
 boolean commandCurrent(Ticket t,long account,String key,long replacement,long version,long duration){
  return dataCurrent(t,account,key,replacement,version,duration)&&t.operationEpoch==operationEpoch;
 }
 void event(Event event){
  if(event==Event.PREPARE){
   if(key==null||originalMuted||attachedEffect!=null||commandedSecondary>0.001f||
      (state!=State.SOURCE_ONLY&&state!=State.PREPARING&&
       state!=State.RECOVERING&&state!=State.TRACK_UNSUPPORTED))
    throw new IllegalStateException("background preparation cannot take active audio ownership");
   state=State.PREPARING;reason="preparing";operationEpoch++;return;
  }
  if(event==Event.PREPARE_READY)return; // data readiness cannot mutate output state
  operationEpoch++;
 }
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
  generation++;pauseEpoch++;operationEpoch++;key=next;
  if(state!=State.STOPPED)state=State.SOURCE_ONLY;
  reason="track_changed";
 }
 void activate(){if(state==State.STOPPED){state=State.SOURCE_ONLY;reason="armed";}}

 void invalidate(String why){
  if(originalMuted)throw new IllegalStateException("boundary cannot discard active output lease");
  generation++;pauseEpoch++;operationEpoch++;key=null;
  if(state!=State.STOPPED)state=State.SOURCE_ONLY;
  reason=why;
 }
 /** Retire decoder callbacks even when recovery retries the exact same song.
  * Source gain restoration on a long pause does NOT retire the decoder. */
 void retireDecoder(){generation++;pauseEpoch++;operationEpoch++;clearSeekFlight();reason="decoder_retired";}
 void preparing(){event(Event.PREPARE);}
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
  /* Installing a verified effect is not a handover. Preserve PREPARING until
     the decoder is ready; only the active playback path may enter ALIGNING. */
  if(state==State.SOURCE_ONLY){state=State.PREPARING;reason="source_effect_ready";}

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
 void stopped(){generation++;pauseEpoch++;operationEpoch++;clearSeekFlight();key=null;originalMuted=false;attachedEffect=null;commandedSecondary=0f;lastVolumePlayer=null;state=State.STOPPED;reason="stopped";}
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
 /** A slow seek may take seconds. The native source must not remain at -100dB
   * while the muted decoder seeks. Keep the verified effect attached (no costly
   * recreation) but restore source gain before seekTo; replacement stays silent. */
 void sourceGainDuringAlignment(DynamicsProcessing effect){
  if(state!=State.ALIGNING||effect==null||effect!=attachedEffect
      ||!effect.hasControl()||!effect.getEnabled()||commandedSecondary>0.001f)
   throw new IllegalStateException("seek source restore requires silent current decoder");
  if(originalMuted){effect.setInputGainAllChannelsTo(0f);originalMuted=false;}
  else effect.setInputGainAllChannelsTo(0f);
  reason="original_audible_during_seek";
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
