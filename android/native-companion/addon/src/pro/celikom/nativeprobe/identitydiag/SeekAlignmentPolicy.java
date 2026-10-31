package pro.celikom.nativeprobe.identitydiag;

import java.util.Arrays;

/**
 * Seek-scoped transport baseline. It preserves a previously stable relationship
 * between the Yandex and replacement clocks and corrects only the new error
 * introduced by a user scrub. It is not an acoustic/Bluetooth latency meter.
 */
final class SeekAlignmentPolicy {
 static final long ACCEPT_RESIDUAL_MS=200;
 static final long MAX_BASELINE_MS=700;
 static final long MAX_DERIVED_BASELINE_MS=MAX_BASELINE_MS+ACCEPT_RESIDUAL_MS;
 static final long STABILITY_SPREAD_MS=45;
 static final long MIN_SAMPLE_INTERVAL_MS=100;
 static final long MIN_SAMPLE_SPAN_MS=250;
 static final long MAX_SAMPLE_GAP_MS=600;
 static final long MAX_BASELINE_AGE_MS=1200;
 private final long[] values=new long[5];
 private final long[] times=new long[5];
 private int count;
 private long lastSampleAt=-1,stableOffset,stableAt=-1,seekOffset;
 private boolean stable,pending,seekOffsetValid;

 void observe(long drift,long now,boolean eligible){
  if(pending||!eligible)return;
  if(Math.abs(drift)>MAX_BASELINE_MS){clear();return;}
  if(count>0&&now-lastSampleAt>MAX_SAMPLE_GAP_MS){clearSamples();stable=false;stableAt=-1;}
  if(stable&&Math.abs(drift-stableOffset)>STABILITY_SPREAD_MS){
   stable=false;stableAt=-1;clearSamples();
  }
  if(count>0&&now-lastSampleAt<MIN_SAMPLE_INTERVAL_MS)return;
  if(count>0){
   long min=drift,max=drift;
   for(int i=0;i<count;i++){min=Math.min(min,values[i]);max=Math.max(max,values[i]);}
   if(max-min>STABILITY_SPREAD_MS)clearSamples();
  }
  if(count==values.length){
   System.arraycopy(values,1,values,0,values.length-1);
   System.arraycopy(times,1,times,0,times.length-1);
   count--;
  }
  values[count]=drift;times[count]=now;count++;lastSampleAt=now;
  if(count>=3&&times[count-1]-times[0]>=MIN_SAMPLE_SPAN_MS){
   long[] sorted=Arrays.copyOf(values,count);Arrays.sort(sorted);
   stableOffset=sorted[count/2];stableAt=now;stable=true;
  }
 }
 void begin(long now){
  if(pending)return;
  pending=true;
  seekOffsetValid=stable&&stableAt>=0&&now>=stableAt&&now-stableAt<=MAX_BASELINE_AGE_MS;
  seekOffset=seekOffsetValid?stableOffset:0;
 }
 boolean pending(){return pending;}
 boolean hasBaseline(){return pending&&seekOffsetValid;}
 long baselineOffset(){return hasBaseline()?seekOffset:0;}
 long adjustedDrift(long rawDrift){return rawDrift-baselineOffset();}
 long steadyDrift(long rawDrift){return rawDrift-(stable?stableOffset:0);}
 long supervisedDrift(long rawDrift){return pending?adjustedDrift(rawDrift):steadyDrift(rawDrift);}
 long decoderTarget(long sourcePosition,long duration){
  long target=sourcePosition-baselineOffset();
  if(duration>0)target=Math.max(0,Math.min(duration-1,target));
  else target=Math.max(0,target);
  return target;
 }
 boolean withinAcceptance(long rawDrift){return Math.abs(adjustedDrift(rawDrift))<=ACCEPT_RESIDUAL_MS;}
 void finish(long rawDrift,long now){
  if(!pending)return;
  pending=false;seekOffsetValid=false;seekOffset=0;clearSamples();
  if(Math.abs(rawDrift)<=MAX_DERIVED_BASELINE_MS){
   stable=true;stableOffset=rawDrift;stableAt=now;
  }else{stable=false;stableAt=-1;}
 }
 void reset(){
  pending=false;seekOffsetValid=false;seekOffset=0;stable=false;stableAt=-1;stableOffset=0;clearSamples();
 }
 private void clearSamples(){count=0;lastSampleAt=-1;}
 private void clear(){clearSamples();stable=false;stableAt=-1;stableOffset=0;}
 long stableOffsetForTest(){return stable?stableOffset:0;}
 boolean stableForTest(){return stable;}
}
