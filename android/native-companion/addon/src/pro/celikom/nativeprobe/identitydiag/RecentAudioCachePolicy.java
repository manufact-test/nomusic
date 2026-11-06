package pro.celikom.nativeprobe.identitydiag;
final class RecentAudioCachePolicy {
 // HONOR Test.44/45: 44 evictions, most on the twelve-entry limit while
 // verified files still fit below 96 MiB. Retain up to sixteen complete
 // editions when their actual byte sizes permit it. The unchanged byte cap
 // still wins for larger songs; partial or stale media is never cached.
 static final int MAX_ENTRIES=16;
 static final long MAX_BYTES=96L*1024L*1024L;
 static boolean shouldTrim(int entries,long bytes){return entries>MAX_ENTRIES||bytes>MAX_BYTES;}
 static String pressure(int entries,long bytes){
  if(entries>MAX_ENTRIES)return "entry_limit";
  if(bytes>MAX_BYTES)return "byte_limit";
  return "none";
 }
 private RecentAudioCachePolicy(){}
}
