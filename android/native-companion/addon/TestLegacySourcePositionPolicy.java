package pro.celikom.nativeprobe.identitydiag;

public final class TestLegacySourcePositionPolicy {
 static int checks;
 static void check(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
 static LegacySourcePositionPolicy.Decision take(LegacySourcePositionPolicy policy,
  String alias,long media,long platform,long platformAge,long now){
  return policy.reconcile(alias,"Дым","Лёша Свик",219000,media,true,
   "Дым","Лёша Свик",219000,platform,platformAge,true,now);
 }
 public static void main(String[] args){
  LegacySourcePositionPolicy policy=new LegacySourcePositionPolicy();
  check(!take(policy,"77",9700,196000,300,10000).override,"never trust one discordant sample");
  LegacySourcePositionPolicy.Decision recovered=take(policy,"77",10000,196300,600,10300);
  check(recovered.override&&recovered.newRecovery&&recovered.position==196300,
   "two fresh matching platform snapshots recover an unreported 3 minute seek");
  check(take(policy,"77",10300,196600,900,10600).override,
   "recovered platform clock continues while Media3 is stale");
  check(take(policy,"77",196600,197000,1200,10900).override==false,
   "normal Media3 clock reclaims authority once it agrees");
  check(!take(policy,"77",197000,197200,1300,11200).override,
   "ordinary jitter never causes a seek");
  check(!take(policy,"77",10000,190000,10000,12000).override,
   "old platform state cannot authorize a new recovery");
  check(!take(policy,"77",10000,10040,400,12300).override,
   "small clock deviations are ignored");
  check(!take(policy,"77",10000,190000,200,13000).override,"first sample after clean state is only candidate");
  check(!take(policy,"88",10000,190000,500,13300).override,
   "a track change cancels a pending fallback");
  check(!LegacySourcePositionPolicy.sameTrack("Дым","Лёша Свик",219000,"Дым","Другой",219000),
   "different artist cannot supply cross-track position");
  check(!LegacySourcePositionPolicy.sameTrack("Дым","Лёша Свик",219000,"Дым","Лёша Свик",210000),
   "different duration cannot supply cross-track position");
  LegacySourcePositionPolicy fresh=new LegacySourcePositionPolicy();
  take(fresh,"77",9700,196000,300,20000);
  check(take(fresh,"77",10000,196300,600,20300).override,"precondition recovery");
  check(fresh.unavailable("77").failClosed,"missing platform controller returns original, not stale Media3");
  check(take(fresh,"77",11000,197000,20000,20400).failClosed,
   "expired platform clock fails closed");
  check(!fresh.unavailable("99").failClosed,
   "track boundary resets fallback lifetime");
  System.out.println("PASS: "+checks+" independent Android platform position fencing checks");
 }
}
