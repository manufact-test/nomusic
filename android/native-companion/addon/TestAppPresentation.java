package pro.celikom.nativeprobe.identitydiag;
import org.json.*;
public class TestAppPresentation {
 static int checks;static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 public static void main(String[] args)throws Exception{
  AppPresentation.Input s=new AppPresentation.Input();AppPresentation p=AppPresentation.of(s);
  check(p.instruction.contains("Войдите")&&!p.connected&&!p.showTrack,"signed-out screen asks for login, no song");
  check(AppPresentation.account(false).equals("Аккаунт · не подключён"),"signed-out account summary");check(AppPresentation.account(true).equals("Аккаунт · подключён"),"connected account summary");
  s.signed=true;p=AppPresentation.of(s);check(p.instruction.contains("Старт")&&!p.showTrack,"account login alone is not an audio connection");
  s.starting=true;p=AppPresentation.of(s);check(p.header.equals("Подключение…")&&!p.connected,"pending access cannot claim working playback");
  s.starting=false;s.running=true;s.enabled=true;p=AppPresentation.of(s);check(p.instruction.contains("Включите песню")&&!p.showTrack,"waiting for Yandex is a connection instruction");
  s.source=true;s.identified=true;p=AppPresentation.of(s);check(p.instruction.contains("эквалайзер")&&!p.showTrack&&p.version.isEmpty(),"reported Ramil case: known metadata without audio connection displays only setup instruction");check(!p.header.equals("Работает")&&!p.connected,"arming is not proof of audio connection");
  s.session=true;s.playing=true;p=AppPresentation.of(s);check(p.instruction.equals("CELIKOM подключён. Можно пользоваться.")&&p.connected&&p.showTrack,"verified connection displays readiness and current song separately");check(!p.header.equals("Подмена активна"),"connected alone does not claim replacement is audible");
  s.preparing=true;p=AppPresentation.of(s);check(p.version.contains("Подготавливаем"),"preparation has its own state");
  s.preparing=false;s.replacing=true;p=AppPresentation.of(s);check(p.header.equals("Подмена активна")&&p.version.equals("Играет версия CELIKOM"),"only actual replacement output shows active");
  s.playing=false;p=AppPresentation.of(s);check(p.header.equals("Подключён")&&p.version.equals("Пауза"),"pause retains connection without claiming playing");
  s.playing=true;s.seeking=true;p=AppPresentation.of(s);check(p.header.equals("Подключён")&&p.version.contains("Синхронизируем"),"seek is not rendered as audible playback");
  s.seeking=false;s.replacing=false;s.missing=true;p=AppPresentation.of(s);check(p.connected&&p.version.contains("Играет оригинал"),"missing catalogue version is not a connection failure");
  s.missing=false;s.confirmation=true;p=AppPresentation.of(s);check(p.version.contains("Подтвердите"),"fallback requires explicit confirmation");
  s.confirmation=false;s.source=false;p=AppPresentation.of(s);check(!p.showTrack&&!p.connected,"connection loss hides the last song");
  s.enabled=false;s.problem="Нет связи. Повторите «Старт».";p=AppPresentation.of(s);check(p.instruction.equals(s.problem)&&!p.showTrack,"start failures remain actionable, not hidden by prior metadata");
  check(AppPresentation.entitlement(new JSONObject().put("allowed",false).put("reason","trial_not_started"),0).contains("после «Старт»"),"trial follows existing desktop Start behavior");
  check(AppPresentation.entitlement(new JSONObject().put("allowed",true).put("source","promo").put("valid_until",JSONObject.NULL),0).equals("Промокод · доступ навсегда"),"existing perpetual promo label");
  String dated=AppPresentation.entitlement(new JSONObject().put("allowed",true).put("source","subscription").put("valid_until","2030-01-02T00:00:00Z"),0);check(dated.startsWith("Подписка до ")&&dated.contains("03:00")&&dated.endsWith("(Москва)"),"existing expiry label uses Moscow time");
  StartIntent intent=new StartIntent();long a=intent.begin();check(intent.current(a),"new Start has a current intent");intent.cancel();check(!intent.current(a)&&!intent.pending,"Stop invalidates an access result already in flight");long b=intent.begin();check(!intent.current(a)&&intent.current(b),"old callback cannot act on a newer Start");intent.cancel();check(!intent.current(b),"logout or activity teardown cancels pending Start");
  System.out.println("PASS: "+checks+" account/connection/playback presentation and delayed Start/Stop checks");
 }
}
