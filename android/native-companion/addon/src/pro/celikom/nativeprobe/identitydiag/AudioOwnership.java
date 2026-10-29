package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
/** Single authority for handover grants and delayed-pause ownership.
 * All audio mutations run through the service's serialized handler thread.
 * Fail open: any release silences replacement before restoring native source.
 */
final class AudioOwnership {
 enum State { SOURCE, PREPARING, ALIGNING, REPLACEMENT, PAUSED, RESTORING }
 private State state=State.SOURCE;
 private long pauseEpoch;
 State state(){return state;}
 void preparing(){state=State.PREPARING;}
 void aligning(){state=State.ALIGNING;}
 void replacement(){state=State.REPLACEMENT;}
 void paused(){state=State.PAUSED;pauseEpoch++;}
 long pauseLease(){return pauseEpoch;}
 boolean validPause(long lease){return state==State.PAUSED&&pauseEpoch==lease;}
 void cancelPause(){pauseEpoch++;if(state==State.PAUSED)state=State.ALIGNING;}
 void source(){state=State.SOURCE;pauseEpoch++;}
 /** Replacement gain may rise only after native input has been fully silenced. */
 void grantReplacement(DynamicsProcessing fx){if(fx==null)throw new IllegalStateException("no verified audio effect");fx.setInputGainAllChannelsTo(-100f);state=State.REPLACEMENT;}
 /** A native gain reset is forbidden until secondary audio has been silenced. */
 void silenceReplacement(MediaPlayer p){state=State.RESTORING;if(p!=null){p.setVolume(0f,0f);if(p.isPlaying())p.pause();}}
 static boolean exclusive(float original,float secondary){return original<=0.001f||secondary<=0.001f;}
}
