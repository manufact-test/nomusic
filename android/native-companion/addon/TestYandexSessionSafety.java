package pro.celikom.nativeprobe.identitydiag;
public final class TestYandexSessionSafety {
 static void check(boolean ok,String reason){if(!ok)throw new AssertionError(reason);}
 public static void main(String[] args){
  String open=YandexSessionSafety.OPEN,close=YandexSessionSafety.CLOSE;
  check(YandexSessionSafety.shouldFailClosed(true,true,open,75561,74313),"Android13 Yandex session replacement must fail closed");
  check(YandexSessionSafety.shouldFailClosed(true,true,close,74313,74313),"closing trusted session must fail closed");
  check(!YandexSessionSafety.shouldFailClosed(true,true,open,74313,74313),"normal per-track OPEN must remain armed");
  check(!YandexSessionSafety.shouldFailClosed(true,true,close,75561,74313),"different CLOSE does not revoke trusted session");
  check(!YandexSessionSafety.shouldFailClosed(true,false,open,75561,74313),"other package ignored");
  check(!YandexSessionSafety.shouldFailClosed(false,true,open,75561,74313),"disarmed remains disarmed");
  check(!YandexSessionSafety.shouldFailClosed(true,true,open,0,74313),"invalid session ignored");
  check(!YandexSessionSafety.shouldFailClosed(true,true,open,75561,-1),"unverified trusted session ignored");
  check(!YandexSessionSafety.shouldFailClosed(true,true,"other",75561,74313),"other broadcast ignored");
  System.out.println("PASS: Yandex session mismatch fail-closed with no auto-trust");
 }
}
