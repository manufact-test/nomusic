package pro.celikom.nativeprobe.identitydiag;

import java.util.HashMap;
import java.util.Map;

/** Persistable, Android-free update discovery state shared by UI and JobService. */
final class UpdateState {
 final long checkedAt;
 final int verifiedInstalledCode;
 final boolean verifiedLatest;
 final int availableCode;
 final String availableManifest;

 private UpdateState(long checked,int installed,boolean latest,int available,String manifest){
  checkedAt=checked;verifiedInstalledCode=installed;verifiedLatest=latest;
  availableCode=available;availableManifest=manifest;
 }
 static UpdateState restore(Map<String,?> values,int installedCode){
  long checked=number(values,"checked",0);
  int verified=(int)number(values,"verifiedInstalledCode",-1);
  boolean latest=Boolean.TRUE.equals(values.get("verifiedLatest"));
  int available=(int)number(values,"availableCode",0);
  Object raw=values.get("availableManifest");
  String manifest=raw instanceof String?(String)raw:null;
  if(available<=installedCode||manifest==null||manifest.trim().isEmpty()){
   available=0;manifest=null;
  }
  return new UpdateState(checked,verified,latest,available,manifest);
 }
 UpdateState successfulCheck(int installedCode,int candidateCode,String manifest,long now){
  boolean available=candidateCode>installedCode&&manifest!=null&&!manifest.trim().isEmpty();
  return new UpdateState(now,installedCode,!available,available?candidateCode:0,available?manifest:null);
 }
 UpdateState afterFailedCheck(){return this;}
 UpdateState afterLater(){return this;}
 UpdateState clearCandidate(){
  return new UpdateState(checkedAt,verifiedInstalledCode,verifiedLatest,0,null);
 }
 boolean hasAvailable(int installedCode){
  return availableCode>installedCode&&availableManifest!=null&&!availableManifest.trim().isEmpty();
 }
 boolean isVerifiedLatestFor(int installedCode){
  return verifiedLatest&&verifiedInstalledCode==installedCode;
 }
 boolean shouldSkipAutomaticCheck(long now,long interval,int installedCode){
  return checkedAt>0&&now>=checkedAt&&now-checkedAt<interval
      &&verifiedInstalledCode==installedCode;
 }
 Map<String,Object> toMap(){
  Map<String,Object> values=new HashMap<>();
  values.put("checked",checkedAt);values.put("verifiedInstalledCode",verifiedInstalledCode);
  values.put("verifiedLatest",verifiedLatest);values.put("availableCode",availableCode);
  values.put("availableManifest",availableManifest);
  return values;
 }
 private static long number(Map<String,?> values,String key,long fallback){
  Object value=values.get(key);return value instanceof Number?((Number)value).longValue():fallback;
 }
}
