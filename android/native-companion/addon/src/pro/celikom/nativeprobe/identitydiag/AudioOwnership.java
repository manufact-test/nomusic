package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.media.audiofx.AudioEffect;
import java.util.Objects;
/** Authoritative audio output permission and lifecycle state, confined to service handler. */
final class AudioOwnership {
 enum State { SOURCE_ONLY, PREPARING, ALIGNING, SAME_SONG_BLEND, REPLACEMENT, PAUSED, RECOVERING, TRACK_UNSUPPORTED, STOPPED }
 /* A single owner distinguishes user pausing from Media3 play-intent buffering. */
 enum PauseMode { NONE, USER, BUFFERING }
 /* Event and ticket authority lives with the sole audio output owner. A data ticket
    survives an ordinary seek/pause, but never a source/account/edition change. */
 enum Event { PREPARE, PREPARE_READY, SEEK, BUFFERING, PAUSE, RESUME, HANDOVER, RETURN, BOUNDARY, ROUTE_LOSS, LOGOUT, STOP }
 static final class Ticket {
  final String sourceKey;
  final long sourceEpoch,operationEpoch,accountEpoch,replacementId,version,durationMs;
  Ticket(String key,long source,long operation,long account,long replacement,long version,long duration){
   sourceKey=key;sourceEpoch=source;operationEpoch=operation;accountEpoch=account;
   replacementId=replacement;this.version=version;durationMs=duration;
  }
 }
 private long operationEpoch=1;
 private PauseMode pauseMode=PauseMode.NONE;
 private boolean handoverAwaitingClock;
 PauseMode pauseMode(){return pauseMode;}
 /* This is the sole handover clock gate, revoked by the same events as output permission. */
 boolean handoverAwaitingClock(){return handoverAwaitingClock;}
 void handoverWaitForClock(boolean value){if(state!=State.ALIGNING)throw new IllegalStateException("not aligning");handoverAwaitingClock=value;}
 void handoverClockValidated(){handoverAwaitingClock=false;}
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
 /* A MediaPlayer completion callback also carries no seek or ownership ID.
    It may originate from a retired position while a native seek/hold is
    running. Only the current playable output state may retire this decoder. */
 boolean mayConsumeCompletion(MediaPlayer p){
  return p!=null&&p!=inFlightDecoder&&!handoverAwaitingClock&&pauseMode==PauseMode.NONE
     &&(state==State.ALIGNING||state==State.SAME_SONG_BLEND||state==State.REPLACEMENT);
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
   handoverAwaitingClock=false;state=State.PREPARING;reason="preparing";operationEpoch++;return;
  }
  if(event==Event.PREPARE_READY)return; // data readiness cannot mutate output state
  handoverAwaitingClock=false;
  if(event==Event.PAUSE)pauseMode=PauseMode.USER;
  else if(event==Event.BUFFERING)pauseMode=PauseMode.BUFFERING;
  else if(event==Event.RESUME||event==Event.ROUTE_LOSS||event==Event.BOUNDARY
      ||event==Event.LOGOUT||event==Event.STOP)pauseMode=PauseMode.NONE;
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
  generation++;pauseEpoch++;operationEpoch++;pauseMode=PauseMode.NONE;handoverAwaitingClock=false;key=next;
  if(state!=State.STOPPED)state=State.SOURCE_ONLY;
  reason="track_changed";
 }
 void activate(){if(state==State.STOPPED){state=State.SOURCE_ONLY;reason="armed";}}

 void invalidate(String why){
  if(originalMuted)throw new IllegalStateException("boundary cannot discard active output lease");
  generation++;pauseEpoch++;operationEpoch++;pauseMode=PauseMode.NONE;handoverAwaitingClock=false;key=null;
  if(state!=State.STOPPED)state=State.SOURCE_ONLY;
  reason=why;
 }
 /** Retire decoder callbacks even when recovery retries the exact same song.
  * Source gain restoration on a long pause does NOT retire the decoder. */
 void retireDecoder(){generation++;pauseEpoch++;operationEpoch++;pauseMode=PauseMode.NONE;clearSeekFlight();handoverAwaitingClock=false;reason="decoder_retired";}
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
 void paused(){if(pauseMode==PauseMode.NONE)pauseMode=PauseMode.USER;state=State.PAUSED;reason=pauseMode==PauseMode.BUFFERING?"buffering":"paused";pauseEpoch++;}
 void hold(boolean buffering){event(buffering?Event.BUFFERING:Event.PAUSE);paused();}
 long pauseLease(){return pauseEpoch;}
 boolean validPause(long lease){return state==State.PAUSED && pauseEpoch==lease;}
 void cancelPause(){pauseEpoch++;pauseMode=PauseMode.NONE;if(state==State.PAUSED){state=State.ALIGNING;reason="resume";}}
 void source(){handoverAwaitingClock=false;state=State.SOURCE_ONLY;pauseMode=PauseMode.NONE;originalMuted=false;attachedEffect=null;commandedSecondary=0f;lastVolumePlayer=null;pauseEpoch++;reason="source_restored";}
 void recovering(String why){handoverAwaitingClock=false;state=State.RECOVERING;pauseEpoch++;reason=why;}
 void unsupported(String why){handoverAwaitingClock=false;state=State.TRACK_UNSUPPORTED;pauseEpoch++;reason=why;}
 void stopped(){generation++;pauseEpoch++;operationEpoch++;pauseMode=PauseMode.NONE;clearSeekFlight();handoverAwaitingClock=false;key=null;originalMuted=false;attachedEffect=null;commandedSecondary=0f;lastVolumePlayer=null;state=State.STOPPED;reason="stopped";}
 void grantReplacement(DynamicsProcessing effect){
  if(key==null||(state!=State.ALIGNING&&state!=State.REPLACEMENT))throw new IllegalStateException("handover requires current aligning track");
  if(inFlightDecoder!=null||handoverAwaitingClock)throw new IllegalStateException("decoder clock/seek must finish before output grant");
  if(effect==null||effect!=attachedEffect||!effect.hasControl()||!effect.getEnabled())
   throw new IllegalStateException("no verified source attenuation");
  // Avoid repeated DSP writes during stable playback polling.
  if(!originalMuted)effect.setInputGainAllChannelsTo(-100f);
  originalMuted=true;state=State.REPLACEMENT;reason="exclusive_grant";
 }
 /** The only exception to exclusive output: a bounded fade between an already
  * advancing, aligned decoder and the verified source of the SAME identity.
  * Callers hold the current track + command ticket throughout every tick.
  * Equal-power gains keep an audible floor, unlike a break-before-make fade. */
 float blendSameSong(MediaPlayer player,DynamicsProcessing effect,float mix,float targetGain,String identity,long ticket,long commandTicket){
  if(!Float.isFinite(mix)||mix<0f||mix>1f)throw new IllegalArgumentException("invalid same-song mix");
  if(!Float.isFinite(targetGain)||targetGain<=0f||targetGain>1f)throw new IllegalArgumentException("invalid replacement gain");
  if(player==null||!player.isPlaying()||!current(ticket,identity)||operationEpoch!=commandTicket||pauseMode!=PauseMode.NONE
      ||(state!=State.ALIGNING&&state!=State.SAME_SONG_BLEND)
      ||inFlightDecoder!=null||handoverAwaitingClock
      ||effect==null||effect!=attachedEffect||!effect.hasControl()||!effect.getEnabled())
   throw new IllegalStateException("same-song blend lacks verified current owner");
  if(state==State.ALIGNING&&commandedSecondary>0.001f)
   throw new IllegalStateException("same-song blend cannot inherit audible decoder");
  float original=(float)Math.cos(Math.PI*mix/2.0);
  float secondary=(float)Math.sin(Math.PI*mix/2.0)*targetGain;
  if(mix==1f){original=0f;secondary=targetGain;}
  // Make the destination audible BEFORE reducing the source; never schedule
  // an interval with both sources near zero, including a delayed Android DSP.
  player.setVolume(secondary,secondary);commandedSecondary=secondary;lastVolumePlayer=player;
  effect.setInputGainAllChannelsTo(original<=0.00001f?-100f:(float)(20.0*Math.log10(original)));
  // The gain approaches zero BEFORE the blend clock reaches its endpoint.
  // Do not enter REPLACEMENT near -60dB before the exact endpoint: the queued final
  // tick must still be authorized as SAME_SONG_BLEND (HONOR 0.3.62 replay).
  originalMuted=mix>=1f;
  state=originalMuted?State.REPLACEMENT:State.SAME_SONG_BLEND;
  reason=originalMuted?"verified_same_song_blend_complete":"verified_same_song_blend";
  return secondary;
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
