package pro.celikom.nativeprobe.identitydiag;

import java.util.Map;

/** Decomposes a MediaPlayer async seek ACK into transport and decoder-cursor facts. */
final class SeekTimingEvidence {
 private SeekTimingEvidence(){}
 static Map<String,Object> atAck(AudioOwnership.SeekAck ack,long ackElapsedRealtimeMs,
                                 long sourceProjectedAtAckMs,long decoderPositionAtAckMs,
                                 long sourceObservedAtAckMs){
  long callback=Math.max(0,ackElapsedRealtimeMs-ack.submittedAt);
  boolean sourceKnown=ack.sourcePositionAtSubmitMs>=0&&sourceProjectedAtAckMs>=0;
  long sourceAdvance=sourceKnown?sourceProjectedAtAckMs-ack.sourcePositionAtSubmitMs:0;
  long landingError=decoderPositionAtAckMs-ack.targetMs;
  return LogStore.map(
    "callbackElapsedMs",callback,
    "sourcePositionAtSubmitMs",sourceKnown?ack.sourcePositionAtSubmitMs:null,
    "sourceAdvanceDuringSeekMs",sourceKnown?sourceAdvance:null,
    "decoderLandingErrorMs",landingError,
    "handoverSkewAtAckMs",sourceKnown?sourceProjectedAtAckMs-decoderPositionAtAckMs:null,
    "sourceAdvanceMinusCallbackMs",sourceKnown?sourceAdvance-callback:null,
    "sourceSnapshotPositionAtSubmitMs",ack.sourceSnapshotPositionAtSubmitMs>=0?ack.sourceSnapshotPositionAtSubmitMs:null,
    "sourceSnapshotAgeAtSubmitMs",ack.sourceObservedAtSubmitMs>=0?Math.max(0,ack.submittedAt-ack.sourceObservedAtSubmitMs):null,
    "sourceSnapshotAgeAtAckMs",sourceObservedAtAckMs>=0?Math.max(0,ackElapsedRealtimeMs-sourceObservedAtAckMs):null,
    "decoderPositionAtSubmitMs",ack.decoderPositionAtSubmitMs>=0?ack.decoderPositionAtSubmitMs:null,
    "rawResidualSemantics","source transport minus decoder cursor at ACK; includes source advance during asynchronous seek",
    "decoderLandingErrorSemantics","decoder cursor minus requested target; not output presentation"
  );
 }
}
