package pro.celikom.nativeprobe.identitydiag;

import java.util.Objects;

/** Debounced trigger for a read-only second Media3 snapshot when platform audio
 * activity disagrees with the long-lived source controller. Counts never pause
 * audio by themselves; only a matching fresh controller snapshot may do that. */
final class SourceActivityProbePolicy {
 enum Action { NONE, PROBE_PAUSE, PROBE_RESUME }
 static final long DEBOUNCE_MS=500, RETRY_MS=4000;
 private String alias;
 private long candidateSince=-1,lastProbeAt=-1;
 private int candidateCount=-1;
 private boolean overrideActive;
 private Action lastProbeAction=Action.NONE;

 Action sample(String nextAlias,boolean sourcePlaying,boolean wantsToPlay,boolean buffering,
               boolean replacementPlaying,boolean replacementAudible,int activeMediaPlayers,
               boolean transportOverrideActive,long now){
  if(nextAlias==null||nextAlias.trim().isEmpty()){reset();return Action.NONE;}
  if(!Objects.equals(alias,nextAlias)){reset();alias=nextAlias;}
  if(overrideActive!=transportOverrideActive){
   overrideActive=transportOverrideActive;candidateSince=-1;candidateCount=-1;
  }
  boolean candidate;
  Action action;
  if(transportOverrideActive){
   candidate=activeMediaPlayers>=2&&sourcePlaying&&wantsToPlay&&!buffering;
   action=Action.PROBE_RESUME;
  }else{
   candidate=activeMediaPlayers==1&&sourcePlaying&&wantsToPlay&&!buffering
     &&replacementPlaying&&replacementAudible;
   action=Action.PROBE_PAUSE;
  }
  if(!candidate){candidateSince=-1;candidateCount=-1;return Action.NONE;}
  if(candidateSince<0||candidateCount!=activeMediaPlayers){
   candidateSince=now;candidateCount=activeMediaPlayers;return Action.NONE;
  }
  if(now-candidateSince<DEBOUNCE_MS||(lastProbeAt>=0&&lastProbeAction==action&&now-lastProbeAt<RETRY_MS))
   return Action.NONE;
  candidateSince=-1;candidateCount=-1;lastProbeAt=now;lastProbeAction=action;return action;
 }

 void probeCompleted(boolean nextOverrideActive,long now){
  overrideActive=nextOverrideActive;candidateSince=-1;candidateCount=-1;lastProbeAt=now;
 }

 void reset(){
  alias=null;candidateSince=-1;lastProbeAt=-1;candidateCount=-1;overrideActive=false;lastProbeAction=Action.NONE;
 }
}
