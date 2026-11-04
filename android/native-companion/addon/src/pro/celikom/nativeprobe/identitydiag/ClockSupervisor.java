package pro.celikom.nativeprobe.identitydiag;
/** One deterministic controller for source-vs-secondary commanded clocks.
 * This does NOT measure speaker/Bluetooth acoustic latency.
 */
final class ClockSupervisor {
 enum Decision { KEEP, SEEK, RESTORE_SOURCE }
 static final long WARN_DRIFT_MS=700, CONFIRM_MS=1500, CORRECTION_DRIFT_MS=1500, CORRECTION_CONFIRM_MS=500, MEDIUM_CONFIRM_MS=650;
 private long unstableSince=-1,severeSince=-1;
 private int severeCorrections;
 Decision assess(boolean aligned,boolean live,boolean sourceJump,long drift,long now){
  if(sourceJump||!aligned){unstableSince=-1;severeSince=-1;return Decision.SEEK;}
  if(!live){resetTransient();return Decision.KEEP;}
  long magnitude=Math.abs(drift);
  // A single healthy sample clears confirmation, never the per-track correction budget.
  if(magnitude<=WARN_DRIFT_MS){resetTransient();return Decision.KEEP;}
  if(unstableSince<0)unstableSince=now;
  if(magnitude>CORRECTION_DRIFT_MS){
   if(severeSince<0)severeSince=now;
   if(now-severeSince>=CORRECTION_CONFIRM_MS && severeCorrections<1){
    severeCorrections++;severeSince=now;return Decision.SEEK;
   }
  }else severeSince=-1;
  // HONOR Test.24: sustained 813 -> 1005ms drift discarded an otherwise
  // healthy decoder until the next song. One muted native seek may recover it;
  // a second sustained divergence still restores the original safely.
  if(now-unstableSince>=MEDIUM_CONFIRM_MS&&severeCorrections<1){
   severeCorrections++;return Decision.SEEK;
  }
  return now-unstableSince>=CONFIRM_MS?Decision.RESTORE_SOURCE:Decision.KEEP;
 }
 /** Do not erase the bounded auto-correction allowance during a seek. */
 void onSeek(){resetTransient();}
 private void resetTransient(){unstableSince=-1;severeSince=-1;}
 void reset(){resetTransient();severeCorrections=0;}
}
