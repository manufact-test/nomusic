package pro.celikom.nativeprobe.identitydiag;
/** Regression from HONOR Test.50: quiet BUFFERING is not a dead session. */
final class Test51SourceControllerRetention {
 static int checks;
 static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
 public static void main(String[] args){
  SourceStateWatchdog s=new SourceStateWatchdog();
  check(!s.observeQuietBuffering("Dym",2,false,0,1000),"first BUFFERING starts observation");
  check(!s.observeQuietBuffering("Dym",2,false,2500,3400),"short buffering is benign");
  check(s.observeQuietBuffering("Dym",2,false,4000,4100),"quiet BUFFERING emits diagnostic");
  check(!s.observeQuietBuffering("Dym",2,false,4500,4400),"diagnostic throttled");
  check(!s.observeQuietBuffering("Dym",2,false,19000,20000),"still throttled");
  check(s.observeQuietBuffering("Dym",2,false,39000,35000),"later observation possible");
  check(!s.observeQuietBuffering("Dym",3,true,0,35100),"PLAYING resets observation");
  check(!s.observeQuietBuffering("Dym",2,false,10000,35200),"new buffering needs dwell");
  check(!s.observeQuietBuffering("Other",2,false,10000,38000),"track change resets dwell");
  check(s.observeQuietBuffering("Other",2,false,12000,67000),"other track can be observed");
  System.out.println("PASS: "+checks+" Test.51 buffering-controller-retention checks");
 }
}
