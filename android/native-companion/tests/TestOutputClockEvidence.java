package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.MediaTimestamp;
import android.os.Build;
import android.os.SystemClock;
import java.util.Map;

/** Pure host evidence tests; no device sound or hardware output is simulated. */
public final class TestOutputClockEvidence {
 static int checks;
 static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
 static long number(Map<String,Object> map,String key){
  Object value=map.get(key);if(!(value instanceof Number))throw new AssertionError("missing numeric "+key+": "+value);
  return ((Number)value).longValue();
 }
 static void seekDecomposition(){
  AudioOwnership.SeekAck alignment=new AudioOwnership.SeekAck(
    AudioOwnership.SeekKind.ALIGNMENT,7,1000,12,221136,false,
    221136,221120,990,220900);
  Map<String,Object> evidence=SeekTimingEvidence.atAck(alignment,1816,221908,221136,1800);
  check(number(evidence,"callbackElapsedMs")==816,"callback duration remains its own measurement");
  check(number(evidence,"sourceAdvanceDuringSeekMs")==772,"source progression during async seek is isolated");
  check(number(evidence,"decoderLandingErrorMs")==0,"decoder landed exactly on the requested target");
  check(number(evidence,"handoverSkewAtAckMs")==772,"current transport skew is still retained separately");
  check(number(evidence,"sourceAdvanceMinusCallbackMs")==-44,"source progression is compared with callback duration");
  check(number(evidence,"sourceSnapshotAgeAtSubmitMs")==10,"source snapshot age at submit is explicit");
  check(number(evidence,"sourceSnapshotAgeAtAckMs")==16,"source snapshot age at ACK is explicit");
  AudioOwnership.SeekAck warm=new AudioOwnership.SeekAck(
    AudioOwnership.SeekKind.WARM,7,2000,13,5070,false,
    5000,4990,1990,4800);
  Map<String,Object> warmEvidence=SeekTimingEvidence.atAck(warm,2077,5077,5070,2070);
  check(number(warmEvidence,"sourceAdvanceDuringSeekMs")==77,"WARM source progression is isolated");
  check(number(warmEvidence,"decoderLandingErrorMs")==0,"WARM decoder landing remains separate from skew");
  check(number(warmEvidence,"handoverSkewAtAckMs")==7,"future lead is not mislabeled as decoder landing error");
 }
 static void outputClockSampling(){
  SystemClock.now=1000;
  Build.VERSION.SDK_INT=36;
  PlaybackSource source=new PlaybackSource("alias","title","artist",10000,"",5000,true,true,1f);
  MediaPlayer player=new MediaPlayer();player.position=5000;
  player.timestamp=new MediaTimestamp(5000000L,System.nanoTime(),1.0f);
  Map<String,Object> available=OutputClockEvidence.capture(player,source,"test");
  check(Boolean.TRUE.equals(available.get("timestampAvailable")),"MediaTimestamp availability is recorded");
  check(number(available,"decoderPositionMs")==5000,"decoder cursor is recorded separately");
  check(number(available,"estimatedPresentedPositionAtSampleMs")>=5000
      &&number(available,"estimatedPresentedPositionAtSampleMs")<=5001,
      "MediaTimestamp is mapped using its own system-nanosecond anchor");
  check(available.get("timestampVsDecoderCursorMs") instanceof Number,
      "presentation estimate and decoder cursor are compared");
  check(available.get("systemToElapsedOffsetNs") instanceof Number,
      "elapsedRealtime and nanoTime are explicitly bridged, not conflated");
  check(Boolean.FALSE.equals(available.get("sourcePcmMeasured"))
      &&Boolean.FALSE.equals(available.get("phaseVerified"))
      &&Boolean.FALSE.equals(available.get("hardwareOutputMeasured")),
      "the new timestamp never claims PCM, phase or speaker proof");
  Build.VERSION.SDK_INT=28;
  Map<String,Object> legacy=OutputClockEvidence.capture(player,source,"api28");
  check(Boolean.TRUE.equals(legacy.get("timestampAvailable")),
      "API 28 uses the still-supported legacy MediaTimestamp system-time accessor");
  player.timestamp=null;
  Map<String,Object> unavailable=OutputClockEvidence.capture(player,source,"unavailable");
  check(Boolean.FALSE.equals(unavailable.get("timestampAvailable")),
      "unavailable platform timestamp is reported honestly");
 }
 public static void main(String[] args){
  seekDecomposition();outputClockSampling();
  System.out.println("PASS: "+checks+" async seek decomposition and MediaTimestamp evidence checks");
 }
}
