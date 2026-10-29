package pro.celikom.nativeprobe.identitydiag;
import android.os.SystemClock;
/** Read-only snapshot shared by the activity and foreground notification. */
final class PlaybackUi {
 static AppPresentation.Input capture(ProbeService p,boolean signed,boolean starting,String problem){
  AppPresentation.Input s=new AppPresentation.Input();s.signed=signed;s.starting=starting;s.running=p!=null&&p.alive();s.problem=problem;
  ReplacementEngine e=p==null?null:p.replacement;PlaybackSource source=s.running?p.current:null;
  s.enabled=e!=null&&e.armed();s.source=fresh(source);s.session=e!=null&&e.trustedSession>0;s.playing=s.source&&source.playing;s.seeking=e!=null&&e.seeking;s.preparing=e!=null&&(e.preparing||e.handoverPending);
  s.identified=e!=null&&s.source&&source.key.equals(e.identityKey)&&e.trackId!=null;s.confirmation=s.identified&&!"ALBUM".equals(e.method)&&!e.confirmed.contains(e.confirmationKey());s.missing=e!=null&&e.descriptor!=null&&!e.descriptor.optBoolean("found");
  if(s.problem.isEmpty()&&e!=null){if(s.source&&e.completedKey!=null&&e.completedKey.equals(source.key)&&e.completedReason!=null)s.problem=e.completedReason;else if(e.status.startsWith("Яндекс сменил"))s.problem="Яндекс Музыка отключилась. Нажмите «Старт» и выберите CELIKOM в её эквалайзере.";else if(e.status.startsWith("Android не")||e.status.startsWith("Телефон не"))s.problem=e.status;else if(e.status.startsWith("Сервер:")||e.status.startsWith("Сеть недоступна"))s.problem="Не удалось получить версию CELIKOM. Играет оригинал; повторим автоматически.";}
  try{s.replacing=e!=null&&e.audioOwner.state()==AudioOwnership.State.REPLACEMENT&&e.effect!=null&&e.player!=null&&e.ready&&!e.returning&&!e.seeking&&e.commandedReplacementVolume>0.001f&&e.player.isPlaying()&&s.playing&&source.key.equals(e.identityKey);}catch(RuntimeException ignored){}
  return s;
 }
 static boolean fresh(PlaybackSource source){long age=source==null?-1:SystemClock.elapsedRealtime()-source.observed;return source!=null&&source.connected&&age>=0&&age<=1500;}
 static MobileActions.Target target(ProbeService p){try{if(p==null||!p.alive()||!fresh(p.current)||p.replacement==null)return null;ReplacementEngine e=p.replacement;if(!p.current.key.equals(e.identityKey)||!"ALBUM".equals(e.method))return null;return new MobileActions.Target(e.trackId,p.current.key,p.current.title,p.current.artist,p.current.duration);}catch(Exception e){return null;}}
}
