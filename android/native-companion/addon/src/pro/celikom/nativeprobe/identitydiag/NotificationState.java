package pro.celikom.nativeprobe.identitydiag;
/** No position countdown: only meaningful state changes rebuild the notification. */
final class NotificationState {
 final String title,text;final boolean suggest;
 NotificationState(String title,String text,boolean suggest){this.title=title;this.text=text;this.suggest=suggest;}
 static NotificationState of(AppPresentation.Input s,String title,String artist,boolean transportLost,boolean sessionLost,boolean exact,boolean hasReplacement){
  if(s.starting)return new NotificationState("CELIKOM","Подключаемся к Яндекс Музыке…",false);
  if(!s.signed)return new NotificationState("CELIKOM","Войдите в аккаунт CELIKOM",false);
  if(sessionLost)return new NotificationState("CELIKOM · потеряно подключение","Откройте эквалайзер Яндекс Музыки, выберите CELIKOM и нажмите «Старт».",false);
  if(!s.enabled)return new NotificationState("CELIKOM","Подмена выключена · играет оригинал",false);
  if(!s.source)return new NotificationState("CELIKOM",transportLost?"Потеряна связь с Яндекс Музыкой · переподключаемся":"Включите песню в Яндекс Музыке",false);
  if(!s.session)return new NotificationState("CELIKOM · требуется подключение","Откройте эквалайзер Яндекс Музыки и выберите CELIKOM.",false);
  AppPresentation p=AppPresentation.of(s);String label=s.identified?safe(title)+(artist==null||artist.trim().isEmpty()?"":" — "+safe(artist)):"CELIKOM";
  String detail=p.version;
  if(s.missing&&!s.replacing)detail="Для этой песни нет замены · играет оригинал";
  if(s.problem.isEmpty()&&!s.playing&&!s.preparing&&!s.confirmation&&!s.seeking)detail=s.missing?"Пауза · для этой песни нет замены":"Пауза";
  if(detail.isEmpty())detail="CELIKOM подключён";
  return new NotificationState(label,detail,s.signed&&exact&&s.identified&&!s.confirmation&&!hasReplacement&&!s.replacing&&!s.preparing&&!s.seeking&&s.problem.isEmpty());
 }
 static String safe(String s){if(s==null)return "";String value=s.replaceAll("[\\x00-\\x1f]"," ").trim();return value.length()>120?value.substring(0,value.offsetByCodePoints(0,Math.min(100,value.codePointCount(0,value.length()))))+"…":value;}
 String fingerprint(){return title+"\u0000"+text+"\u0000"+suggest;}
}
