package pro.celikom.nativeprobe.identitydiag;
public class TestTransitionRecovery {
 static int checks;static void check(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
 public static void main(String[] args){
  SourceTransitionGate gate=new SourceTransitionGate();
  check(gate.sample("9",75)==SourceTransitionGate.ACCEPT,"initial current source accepted");
  check(gate.begin("1",3939),"recorded stale alias event starts a safety boundary");
  check(gate.sample("9",3946)==SourceTransitionGate.WAIT,"old or mismatched snapshot cannot play across boundary");
  check(!gate.begin("1",4500),"repeated event cannot reset the deadline");
  check(gate.sample("9",4939)==SourceTransitionGate.REFRESH,"report mismatch schedules fresh controller after one second rather than waiting until user Stop at 135090ms");
  gate.clear();check(gate.sample("9",5100)==SourceTransitionGate.ACCEPT,"fresh connection clears old alias wait and uses its authoritative snapshot");
  gate.begin("10",5200);check(gate.sample("9",5250)==SourceTransitionGate.WAIT,"genuine transition still fences old item");check(gate.sample("10",5300)==SourceTransitionGate.ACCEPT&&!gate.pending,"matching new item immediately unlocks");
  gate.begin("9",5500);check(gate.sample(null,5600)==SourceTransitionGate.WAIT,"matching alias with idle/empty metadata is not a usable transition snapshot");check(gate.sample(null,6500)==SourceTransitionGate.REFRESH,"missing usable metadata also expires the transition gate");gate.clear();
  gate.begin("10",6000);gate.begin("11",6500);check(gate.sample("10",6800)==SourceTransitionGate.WAIT,"rapid Next follows newest expected item");check(gate.sample("12",7500)==SourceTransitionGate.REFRESH,"new mismatch also has a bounded deadline");
  gate.clear();gate.begin(null,8000);check(gate.sample("13",8001)==SourceTransitionGate.ACCEPT,"missing alias cannot create an indefinite gate");
  BufferRecoveryGate recovery=new BufferRecoveryGate();
  check(!recovery.recover(true,true,false,1000,0),"lookahead starts observation only");check(!recovery.recover(true,true,false,1250,250),"position progress cancels false underflow");check(!recovery.recover(true,true,false,1500,500),"advancing decoder keeps original muted");check(!recovery.recover(true,true,false,1500,750),"brief stalled read is tolerated");check(recovery.recover(true,true,false,1500,1000),"sustained stalled playback still restores original");check(!recovery.recover(true,false,true,1500,1100),"pending seek is not cancelled as a buffer stall");check(!recovery.recover(false,true,false,1600,1200),"buffer completion resets recovery gate");
  System.out.println("PASS: "+checks+" recorded alias mismatch and decoder-progress recovery checks");
 }
}
