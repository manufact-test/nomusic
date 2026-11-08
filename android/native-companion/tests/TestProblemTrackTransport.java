package pro.celikom.nativeprobe.identitydiag;
public final class TestProblemTrackTransport {
 static int checks=0;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 public static void main(String[] args){
  check(ProblemTrackTransport.isKnownStaleMedia3Track("42884423"),"RASKOL known missing pause");
  check(ProblemTrackTransport.isKnownStaleMedia3Track("39949113"),"Dym known missing seek");
  check(!ProblemTrackTransport.isKnownStaleMedia3Track("42498653"),"ordinary tracks unchanged");
  check(!ProblemTrackTransport.isKnownStaleMedia3Track(null),"null is never eligible");
  check(ProblemTrackTransport.eligible("42884423",true,true,true,true),"verified running track eligible");
  check(!ProblemTrackTransport.eligible("42884423",true,false,true,true),"not yet prepared");
  check(!ProblemTrackTransport.eligible("42884423",false,true,true,true),"not armed");
  check(!ProblemTrackTransport.eligible("42884423",true,true,false,true),"not connected");
  check(!ProblemTrackTransport.eligible("42884423",true,true,true,false),"signed out");
  check(ProblemTrackTransport.target(50000,232330,true)==80000,"forward 30sec");
  check(ProblemTrackTransport.target(50000,232330,false)==20000,"backward 30sec");
  check(ProblemTrackTransport.target(5000,232330,false)==0,"negative target clamped");
  check(ProblemTrackTransport.target(222000,232330,true)==232230,"tail clamped");
  check(ProblemTrackTransport.target(1,0,true)==-1,"unknown duration rejected");
  check(ProblemTrackTransport.isAction(ProblemTrackTransport.TOGGLE),"pause/play action");
  check(ProblemTrackTransport.isAction(ProblemTrackTransport.BACK),"back action");
  check(ProblemTrackTransport.isAction(ProblemTrackTransport.FORWARD),"forward action");
  check(ProblemTrackTransport.isAction(ProblemTrackTransport.NEXT),"next action");
  check(!ProblemTrackTransport.isAction("stop"),"existing stop action unaffected");
  System.out.println("PASS: "+checks+" missing-Media3-event fallback transport policies");
 }
}
