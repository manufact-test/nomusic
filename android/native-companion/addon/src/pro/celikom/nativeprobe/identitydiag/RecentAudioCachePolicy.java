package pro.celikom.nativeprobe.identitydiag;
final class RecentAudioCachePolicy {
 static final int MAX_ENTRIES=12;
 static final long MAX_BYTES=128L*1024L*1024L;
 static boolean shouldTrim(int entries,long bytes){return entries>MAX_ENTRIES||bytes>MAX_BYTES;}
 static String pressure(int entries,long bytes){
  if(entries>MAX_ENTRIES)return "entry_limit";
  if(bytes>MAX_BYTES)return "byte_limit";
  return "none";
 }
 private RecentAudioCachePolicy(){}
}
