package pro.celikom.nativeprobe.identitydiag;
/** No position countdown: only meaningful state changes rebuild the notification. */
final class NotificationState {
 final String title,text;final boolean suggest;
 NotificationState(String title,String text,boolean suggest){this.title=title;this.text=text;this.suggest=suggest;}
 /** The Media3 controller can report buffering while playWhenReady=true.
  * Neither a PAUSE label nor an old track title is trustworthy in this state.
  * Passive display only: never play/pause/seek Yandex or touch native audio. */
 static NotificationState yandexBuffering(boolean stale){
  return new NotificationState(stale?"CELIKOM · Яндекс не отвечает":"CELIKOM",
    stale?"Яндекс не обновляет трек · играет оригинал":
      "Яндекс загружает · играет оригинал",false);
 }
 static NotificationState of(AppPresentation.Input s,String title,String artist,boolean transportLost,boolean sessionLost,boolean exact,boolean hasReplacement){
  if(s.starting)return new NotificationState("CELIKOM","Подключаемся к Яндекс Музыке…",false);
  if(!s.signed)return new NotificationState("CELIKOM","Войдите в аккаунт CELIKOM",false);
  if(sessionLost)return new NotificationState("CELIKOM · потеряно подключение","Откройте эквалайзер Яндекс Музыки, выберите CELIKOM и нажмите «Старт».",false);
  if(!s.enabled)return new NotificationState("CELIKOM","Подмена выключена · играет оригинал",false);
  if(!s.source)return new NotificationState("CELIKOM",transportLost?"Потеряна связь с Яндекс Музыкой · переподключаемся":"Включите песню в Яндекс Музыке",false);
  if(!s.session)return new NotificationState("CELIKOM · требуется подключение","Откройте эквалайзер Яндекс Музыки и выберите CELIKOM.",false);
  AppPresentation p=AppPresentation.of(s);String label=title==null||title.trim().isEmpty()?"CELIKOM":safe(title)+(artist==null||artist.trim().isEmpty()?"":" — "+safe(artist));
  String detail=p.version;
  // A complete APPROVED-only snapshot can rule out an approved version,
  // but cannot establish submission/moderation status. Keep the compact
  // Android notification readable; the Activity retains full context.
  if(!s.identified&&s.catalogueFresh&&"NO_MATCH".equals(s.catalogueStatus)&&s.playing
      &&!"album_region_restricted".equals(s.identityReason))
    detail="Не удалось сопоставить версию · играет оригинал";
  if(s.missing&&!s.replacing)detail="Для этой песни нет замены · играет оригинал";
  if(s.problem.isEmpty()&&!s.playing&&!s.preparing&&!s.seeking){
    boolean noApproved=!s.identified&&s.catalogueFresh&&"NO_MATCH".equals(s.catalogueStatus)
      &&!"album_region_restricted".equals(s.identityReason);
    boolean unknown=!s.identified&&!s.identityReason.isEmpty()&&!"waiting_for_album_response".equals(s.identityReason);
    detail=s.missing?"Пауза · для этой песни нет замены":noApproved?"Пауза · совпадение не найдено":unknown?"Пауза · не удалось проверить версию":"Пауза";
   }
  if(detail.isEmpty())detail="CELIKOM подключён";
  return new NotificationState(label,detail,s.signed&&exact&&s.identified&&!hasReplacement&&!s.replacing&&!s.preparing&&!s.seeking&&s.problem.isEmpty());
 }
 static String safe(String s){if(s==null)return "";String value=s.replaceAll("[\\x00-\\x1f]"," ").trim();return value.length()>120?value.substring(0,value.offsetByCodePoints(0,Math.min(100,value.codePointCount(0,value.length()))))+"…":value;}
 String fingerprint(){return title+"\u0000"+text+"\u0000"+suggest;}
}
