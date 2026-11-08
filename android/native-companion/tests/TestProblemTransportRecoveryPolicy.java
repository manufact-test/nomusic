package pro.celikom.nativeprobe.identitydiag;
public final class TestProblemTransportRecoveryPolicy {
 static int checks;
 static void check(boolean cond,String why){checks++;if(!cond)throw new AssertionError(why);}
 public static void main(String[] args){
  ProblemTransportRecoveryPolicy p=new ProblemTransportRecoveryPolicy();
  long ticket=p.arm("626","42884423",1000);
  check(!p.consumeRetry(ticket,"626","42884423",1700,true),"must observe confirmed pause");
  check(p.confirm(ticket,"626","42884423",1250,true),"initial pause verified");
  check(!p.consumeRetry(ticket,"626","42884423",1390,true),"cannot reissue before bounced window");
  check(!p.consumeRetry(ticket,"626","42884423",1710,false),"native still paused");
  check(!p.consumeRetry(ticket,"other","42884423",1710,true),"alias change must not retry");
  check(!p.consumeRetry(ticket,"626","39949113",1710,true),"track change must not retry");
  check(p.consumeRetry(ticket,"626","42884423",1710,true),"confirmed bounce merits one guarded retry");
  check(!p.consumeRetry(ticket,"626","42884423",1720,true),"at most one command");
  long next=p.arm("626","42884423",2000);
  check(!p.confirm(ticket,"626","42884423",2200,true),"stale pending callbacks invalid");
  check(p.confirm(next,"626","42884423",2250,true),"new pause verified");
  check(!p.consumeRetry(next,"626","42884423",3600,true),"retry window expired");
  p.cancel();
  check(!p.consumeRetry(next,"626","42884423",2700,true),"later explicit play cancels retry");
  System.out.println("PASS: "+checks+" one-shot Yandex pause-bounce guard checks");
 }
}
