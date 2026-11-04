package pro.celikom.nativeprobe.identitydiag;
final class RecentAudioCachePolicy {
 // HONOR Test.32: all ten long-browse evictions were caused by the old
 // eight-entry limit while the 96 MiB byte ceiling still had room. Keep
 // another few verified complete files for shuffled album/repeat selections;
 // never increase the private disk budget or allow partial sparse reuse.
 static final int MAX_ENTRIES=12;
 static final long MAX_BYTES=96L*1024L*1024L;
 static boolean shouldTrim(int entries,long bytes){return entries>MAX_ENTRIES||bytes>MAX_BYTES;}
 static String pressure(int entries,long bytes){
  if(entries>MAX_ENTRIES)return "entry_limit";
  if(bytes>MAX_BYTES)return "byte_limit";
  return "none";
 }
 private RecentAudioCachePolicy(){}
}
