package pro.celikom.nativeprobe.identitydiag;
public class TestNotifications {
 static int checks;static void check(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
 static NotificationState state(AppPresentation.Input s,boolean transportLost,boolean sessionLost,boolean exact,boolean has){return NotificationState.of(s,"Песня","Исполнитель",transportLost,sessionLost,exact,has);}
 public static void main(String[] args){
  AppPresentation.Input s=new AppPresentation.Input();s.starting=true;NotificationState n=state(s,false,false,false,false);check(n.text.contains("Подключаемся")&&!n.suggest,"initial foreground notification does not claim connected playback");
  s.starting=false;n=state(s,false,false,true,false);check(n.text.contains("Войдите")&&!n.suggest,"logged-out actions cannot suggest songs");
  s.signed=true;s.running=true;n=state(s,false,false,true,false);check(n.text.contains("выключена")&&!n.suggest,"manual bypass retains an honest original status");
  s.enabled=true;n=state(s,false,false,true,false);check(n.text.contains("Включите песню")&&!n.suggest,"initial wait is not called a disconnect");n=state(s,true,false,true,false);check(n.text.contains("Потеряна связь")&&!n.suggest,"transport loss is distinguishable from absence of a replacement");
  s.source=true;s.identified=true;s.playing=true;n=state(s,false,false,true,false);check(n.title.contains("требуется подключение")&&!n.title.contains("Песня")&&!n.suggest,"unverified audio session shows setup, not stale metadata");
  s.session=true;s.missing=true;n=state(s,false,false,true,false);check(n.title.equals("Песня — Исполнитель")&&n.text.contains("нет замены")&&n.suggest,"current exact song without a replacement exposes Suggest");
  check(!state(s,false,false,false,false).suggest,"metadata/fallback target cannot be submitted as an exact song");check(!state(s,false,false,true,true).suggest,"existing replacement hides redundant Suggest");
  s.missing=false;s.replacing=true;n=state(s,false,false,true,true);check(n.text.equals("Играет версия CELIKOM")&&!n.suggest,"actual replacement is reported as active");
  s.playing=false;n=state(s,false,false,true,true);check(n.text.equals("Пауза")&&!n.suggest,"pause is not called a disconnect");
  s.replacing=false;s.missing=true;n=state(s,false,false,true,false);check(n.text.contains("Пауза")&&n.text.contains("нет замены")&&n.suggest,"a paused exact missing song remains suggestible");
  s.playing=true;s.preparing=true;n=state(s,false,false,true,false);check(!n.suggest,"preparing audio cannot expose a conflicting contribution action");
  s.preparing=false;s.missing=false;s.seeking=true;n=state(s,false,false,true,true);check(n.text.contains("Синхронизируем")&&!n.suggest,"seek status is distinct from connection loss");
  s.seeking=false;s.confirmation=true;n=state(s,false,false,true,false);check(n.text.contains("Подтвердите")&&!n.suggest,"ambiguous identity is never auto-submitted");
  s.confirmation=false;s.problem="Не удалось получить версию CELIKOM. Играет оригинал; повторим автоматически.";n=state(s,false,false,true,false);check(n.text.equals(s.problem)&&!n.suggest,"backend failure is not falsely labelled a missing song");
  s.problem="";s.enabled=false;n=state(s,false,true,true,false);check(n.title.contains("потеряно подключение")&&n.text.contains("эквалайзер")&&!n.suggest,"lost audio session asks for the actual recovery action");
  s.enabled=true;s.session=true;s.source=true;s.identified=true;s.playing=true;NotificationState first=state(s,false,false,true,false),same=state(s,false,false,true,false);check(first.fingerprint().equals(same.fingerprint()),"unchanged state does not require notification churn");s.replacing=true;check(!first.fingerprint().equals(state(s,false,false,true,true).fingerprint()),"audio phase changes trigger a notification update");
  s.replacing=false;s.source=false;n=state(s,true,false,true,false);check(!n.title.contains("Песня")&&!n.suggest,"source disappearance removes title and action together");
  NotificationTarget pinned=new NotificationTarget("run-one","123","song-key",7);
  check(pinned.matches("run-one","123","song-key",7),"current notification action is valid");
  check(!pinned.matches("run-one","456","another-song",7),"next song cannot replace the song pinned by the action");check(!pinned.matches("run-one","456","song-key",7),"track ID is checked independently of metadata");check(!pinned.matches("run-one","123","changed-edition",7),"edition change invalidates an old action");check(!pinned.matches("run-two","123","song-key",7),"service restart invalidates old notification actions");check(!pinned.matches("run-one","123","song-key",8),"account change invalidates old actions");check(!new NotificationTarget(null,null,null,-1).matches("run-one","123","song-key",7),"missing intent extras fail closed");
  check(pinned.fingerprint().equals(new NotificationTarget("run-one","123","song-key",7).fingerprint()),"same target keeps a stable PendingIntent identity");
  check(!pinned.fingerprint().equals(new NotificationTarget("run-one","456","song-key",7).fingerprint()),"different ID has a different PendingIntent identity");check(!pinned.fingerprint().equals(new NotificationTarget("run-two","123","song-key",7).fingerprint()),"different run has a different PendingIntent identity");check(!pinned.fingerprint().equals(new NotificationTarget("run-one","123","song-key",8).fingerprint()),"different account epoch has a different PendingIntent identity");
  check(pinned.fingerprint().matches("[a-f0-9]{64}")&&!pinned.fingerprint().contains("song-key"),"notification identity URI contains no raw song metadata");check(!NotificationState.safe("Песня\nСтрока\r").contains("\n"),"notification labels have no injected lines");
  System.out.println("PASS: "+checks+" notification state, action visibility and pinned song/account/run checks");
 }
}
