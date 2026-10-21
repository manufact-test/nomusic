package pro.celikom.nativeprobe.identitydiag;
import java.text.*;
import java.util.*;
import org.json.*;
/** Account, connection and audio states have separate meanings on screen. */
final class AppPresentation {
 static final class Input {
  boolean signed,starting,running,enabled,source,session,playing,replacing,seeking,preparing,identified,confirmation,missing;
  String problem="";
 }
 final String header,instruction,version;final boolean connected,showTrack;
 AppPresentation(String header,String instruction,String version,boolean connected,boolean showTrack){this.header=header;this.instruction=instruction;this.version=version;this.connected=connected;this.showTrack=showTrack;}
 static AppPresentation of(Input s){
  if(s.starting)return new AppPresentation("Подключение…","Подключаем CELIKOM…","",false,false);
  if(!s.signed)return new AppPresentation("Не подключён","Войдите в аккаунт CELIKOM, чтобы начать.","",false,false);
  if(!s.running||!s.enabled)return new AppPresentation(s.running?"Оригинал":"Остановлен",s.problem.isEmpty()?"Нажмите «Старт», чтобы подключить CELIKOM.":s.problem,"",false,false);
  if(!s.source)return new AppPresentation("Ожидание музыки","Включите песню в Яндекс Музыке.","",false,false);
  if(!s.session)return new AppPresentation("Не подключён","Откройте эквалайзер Яндекс Музыки и выберите CELIKOM.","",false,false);
  String detail;
  if(s.confirmation)detail="Подтвердите найденную песню, чтобы включить её подмену.";
  else if(!s.identified)detail="Определяем песню…";
  else if(s.seeking)detail="Синхронизируем позицию…";
  else if(s.replacing)detail=s.playing?"Играет версия CELIKOM":"Пауза";
  else if(s.missing)detail="Версия CELIKOM ещё не загружена. Играет оригинал.";
  else if(!s.problem.isEmpty())detail=s.problem;
  else if(s.preparing)detail="Подготавливаем версию CELIKOM…";
  else if(!s.playing)detail="Пауза в Яндекс Музыке";
  else detail="Играет оригинал";
  return new AppPresentation(s.replacing&&s.playing&&!s.seeking?"Подмена активна":"Подключён","CELIKOM подключён. Можно пользоваться.",detail,true,s.identified);
 }
 static String account(boolean signed){return signed?"Аккаунт · подключён":"Аккаунт · не подключён";}
 static String entitlement(JSONObject access,long now){
  if(access==null)return "";
  if(access.optBoolean("allowed")){
   String source=access.optString("source"),until=access.optString("valid_until");
   if("promo".equals(source)&&(access.isNull("valid_until")||until.isEmpty()))return "Промокод · доступ навсегда";
   try{SimpleDateFormat parser=new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'",Locale.ROOT);parser.setTimeZone(TimeZone.getTimeZone("UTC"));parser.setLenient(false);Date date=parser.parse(until);if(date!=null&&date.getTime()>now){SimpleDateFormat format=new SimpleDateFormat("d MMMM, HH:mm",new Locale("ru"));format.setTimeZone(TimeZone.getTimeZone("Europe/Moscow"));return ("promo".equals(source)?"Промокод до ":"subscription".equals(source)?"Подписка до ":"Пробный период до ")+format.format(date)+" (Москва)";}}catch(ParseException ignored){}
   return "Доступ разрешён";
  }
  switch(access.optString("reason")){case "trial_not_started":return "3 дня пробного периода начнутся после «Старт»";case "email_unverified":return "Подтвердите email, чтобы начать";case "service_incident":return "Сбой интеграции · время доступа будет компенсировано";case "account_disabled":return "Доступ к аккаунту отключён";default:return "subscription".equals(access.optString("source"))?"Подписка завершена":"Пробный период завершён";}
 }
}
