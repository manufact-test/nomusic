package pro.celikom.nativeprobe.identitydiag;
/** Regression for 2026-11-08 HONOR Test.64: a finished album lookup must not
 * leave the notification in the infinite "Определяем песню" state. */
public final class TestIdentificationStatus {
 static int checks=0;
 static void ok(boolean assertion,String message){checks++;if(!assertion)throw new AssertionError(message);}
 static AppPresentation.Input input(){
  AppPresentation.Input s=new AppPresentation.Input();
  s.signed=true;s.running=true;s.enabled=true;s.source=true;s.session=true;s.playing=true;
  return s;
 }
 static void has(String actual,String part,String why){ok(actual.contains(part),why+"; actual="+actual);}
 public static void main(String[] args){
  AppPresentation.Input pending=input();pending.identityReason="waiting_for_album_response";
  has(AppPresentation.of(pending).version,"Проверяем наличие версии CELIKOM","Album request in flight");
  NotificationState pn=NotificationState.of(pending,"Малая, пой","Мари Краймбрери",false,false,false,false);
  has(pn.text,"Проверяем наличие версии CELIKOM","Pending notification");
  has(pn.title,"Малая, пой","Even unknown ID must show the known Yandex title");
  ok(!pn.suggest,"No suggestion button without an authoritative ID");

  AppPresentation.Input region=input();region.identityReason="album_region_restricted";
  String regionStatus=AppPresentation.of(region).version;
  has(regionStatus,"Яндекс ограничил","451 is a terminal identification failure");
  region.catalogueFresh=true;
  region.catalogueStatus="NO_MATCH";
  has(AppPresentation.of(region).version,"Яндекс ограничил",
    "451 must not be overwritten by fresh catalogue NO_MATCH");
  ok(!AppPresentation.of(region).version.contains("не найдена"),
    "451 cannot be presented as proof that approved replacement is missing");
  ok(!regionStatus.contains("Определяем")&&!regionStatus.contains("нет замены"),"451 cannot imply an absent CELIKOM replacement");
  NotificationState rn=NotificationState.of(region,"Малая, пой","Мари Краймбрери",false,false,false,false);
  has(rn.text,"Яндекс ограничил","451 must show a cause in the notification");
  ok(!rn.text.contains("Нет одобренной версии"),
    "current song 451 never implies absent approved replacement");
  ok(!rn.suggest,"Unknown Track ID must not allow sending a song request");

  AppPresentation.Input unmatched=input();unmatched.identityReason="no_unique_candidate";
  has(AppPresentation.of(unmatched).version,"Не удалось проверить версию CELIKOM","Completed, no unique candidate");
  AppPresentation.Input ambiguous=input();ambiguous.identityReason="album_ambiguous_weaker_fallback_withheld";
  has(AppPresentation.of(ambiguous).version,"однозначно определить","Ambiguous album is not an absent song");
  region.playing=false;
  has(NotificationState.of(region,"ИСКАЛА","Земфира",false,false,false,false).text,"не удалось проверить версию","Paused terminal state stays terminal");

  AppPresentation.Input missing=input();missing.identified=true;missing.missing=true;
  has(AppPresentation.of(missing).version,"ещё не загружена","Only successful live resolve found=false permits no replacement");
  has(NotificationState.of(missing,"Трек","Артист",false,false,true,false).text,"нет замены","Keep old absence status");
  ok(NotificationState.of(missing,"Трек","Артист",false,false,true,false).suggest,"Known album identity can still suggest missing song");

  AppPresentation.Input active=input();active.identified=true;active.replacing=true;
  has(NotificationState.of(active,"Трек","Артист",false,false,true,true).text,"Играет версия CELIKOM","Existing successful replacement preserved");
  AppPresentation.Input lost=input();lost.source=false;
  has(NotificationState.of(lost,"Трек","Артист",true,false,false,false).text,"переподключаемся","Existing disconnect recovery preserved");
  System.out.println("PASS: identification-status terminal/pending/451/missing/replacing/paused, checks="+checks);
 }
}
