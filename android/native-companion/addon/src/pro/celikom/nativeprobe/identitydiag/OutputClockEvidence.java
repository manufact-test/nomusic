package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.MediaTimestamp;
import android.os.Build;
import android.os.SystemClock;
import java.util.Map;

/**
 * Passive evidence from the CELIKOM-owned MediaPlayer only.
 * MediaTimestamp is an OS-reported presentation-clock estimate, not speaker/BT PCM.
 */
final class OutputClockEvidence {
 private OutputClockEvidence(){}
 static Map<String,Object> capture(MediaPlayer player,PlaybackSource source,String stage){
  long systemBefore=System.nanoTime();
  long elapsedBefore=SystemClock.elapsedRealtimeNanos();
  long decoderPosition=-1;
  MediaTimestamp timestamp=null;
  String unavailableReason=null;
  try{
   if(player==null)unavailableReason="player_unavailable";
   else{
    decoderPosition=player.getCurrentPosition();
    if(Build.VERSION.SDK_INT>=23)timestamp=player.getTimestamp();
    else unavailableReason="api_below_23";
    if(timestamp==null&&unavailableReason==null)unavailableReason="timestamp_unavailable";
   }
  }catch(RuntimeException error){
   unavailableReason="player_state_"+error.getClass().getSimpleName();
  }
  long elapsedAfter=SystemClock.elapsedRealtimeNanos();
  long systemAfter=System.nanoTime();
  long sampleSystem=(systemBefore+systemAfter)/2;
  long sampleElapsed=(elapsedBefore+elapsedAfter)/2;
  long sampleElapsedMs=sampleElapsed/1000000L;
  long sourcePosition=-1,sourceAge=-1;
  if(source!=null){
   sourceAge=Math.max(0,sampleElapsedMs-source.observed);
   double projected=source.position+(source.playing?sourceAge*(double)source.speed:0d);
   sourcePosition=Math.max(0,Math.min(source.duration,Math.round(projected)));
  }
  Map<String,Object> fields=LogStore.map(
    "stage",stage,
    "outputClockMethod","MediaPlayer.getTimestamp",
    "outputClockOwner","CELIKOM replacement MediaPlayer",
    "timestampAvailable",timestamp!=null,
    "timestampUnavailableReason",unavailableReason,
    "sampleSystemClock","System.nanoTime",
    "sampleElapsedClock","SystemClock.elapsedRealtimeNanos",
    "sampleSystemNanoTime",sampleSystem,
    "sampleElapsedRealtimeNanoTime",sampleElapsed,
    "systemToElapsedOffsetNs",sampleElapsed-sampleSystem,
    "sampleWindowSystemNs",Math.max(0,systemAfter-systemBefore),
    "sampleWindowElapsedNs",Math.max(0,elapsedAfter-elapsedBefore),
    "decoderPositionMs",decoderPosition,
    "sourceTransportPositionAtSampleMs",source==null?null:sourcePosition,
    "sourceSnapshotPositionMs",source==null?null:source.position,
    "sourceSnapshotAgeAtSampleMs",source==null?null:sourceAge,
    "sourceSnapshotObservedElapsedRealtimeMs",source==null?null:source.observed,
    "sourcePlaying",source!=null&&source.playing,
    "sourceSpeed",source==null?null:source.speed,
    "sourceOutputTimestampAvailable",false,
    "sourcePcmMeasured",false,
    "phaseVerified",false,
    "hardwareOutputMeasured",false,
    "measurementScope","replacement_media_clock_only"
  );
  if(timestamp!=null){
   long anchorSystemNs=Build.VERSION.SDK_INT>=29
      ?timestamp.getAnchorSystemNanoTime():timestamp.getAnchorSytemNanoTime();
   long anchorMediaUs=timestamp.getAnchorMediaTimeUs();
   float rate=timestamp.getMediaClockRate();
   long deltaNs=sampleSystem-anchorSystemNs;
   double estimated=anchorMediaUs/1000d+(deltaNs/1000000d)*rate;
   long estimatedMs=Math.round(estimated);
   fields.put("mediaTimestampAnchorTimebase","MediaTimestamp system nanoseconds");
   fields.put("mediaTimestampAnchorMediaTimeUs",anchorMediaUs);
   fields.put("mediaTimestampAnchorSystemNanoTime",anchorSystemNs);
   fields.put("mediaTimestampClockRate",rate);
   fields.put("mediaTimestampAnchorDeltaNs",deltaNs);
   fields.put("estimatedPresentedPositionAtSampleMs",estimatedMs);
   fields.put("timestampVsDecoderCursorMs",decoderPosition<0?null:estimatedMs-decoderPosition);
   fields.put("timestampVsSourceTransportMs",source==null?null:estimatedMs-sourcePosition);
  }
  return fields;
 }
}
