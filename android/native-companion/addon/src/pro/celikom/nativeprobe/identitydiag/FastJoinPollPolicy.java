package pro.celikom.nativeprobe.identitydiag;
/** Bounded read-only source sampling while the freshly prepared decoder is still inaudible. */
final class FastJoinPollPolicy {
 static final long BUDGET_MS=1200, STEP_MS=60, INITIAL_MS=35;
 static boolean eligible(boolean alive,long now,long deadline,boolean armed,
                         boolean hasDecoder,boolean ready,boolean hasEffect,
                         boolean trustedSession,boolean sourcePlaying,boolean sameIdentity){
  return alive&&now<=deadline&&armed&&hasDecoder&&ready&&!hasEffect
   &&trustedSession&&sourcePlaying&&sameIdentity;
 }
}
