package pro.celikom.nativeprobe.identitydiag;
public final class TestRecentAudioCachePolicy {
 static int checks;
 static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 public static void main(String[] args){
  long mb=1024L*1024L;
  check(RecentAudioCachePolicy.MAX_ENTRIES==16,"sixteen bounded verified complete files for longer shuffled sessions");
  check(RecentAudioCachePolicy.MAX_BYTES==96L*mb,"bounded private file cache");
  check(!RecentAudioCachePolicy.shouldTrim(16,96L*mb),"exact entry limit retained when bytes fit");
  check(!RecentAudioCachePolicy.shouldTrim(6,78L*mb),"six recent songs retained across a playlist change");
  check(!RecentAudioCachePolicy.shouldTrim(9,60L*mb),"ninth file stays while disk ceiling has capacity");
  check(!RecentAudioCachePolicy.shouldTrim(13,60L*mb),"thirteenth complete file retained with free byte budget");
  check(RecentAudioCachePolicy.shouldTrim(17,60L*mb),"seventeenth file trimmed even with free byte budget");
  check(RecentAudioCachePolicy.shouldTrim(5,96L*mb+1),"byte ceiling enforced");
  check("entry_limit".equals(RecentAudioCachePolicy.pressure(17,97L*mb)),"entry pressure first");
  check("byte_limit".equals(RecentAudioCachePolicy.pressure(5,97L*mb)),"byte pressure");
  check("none".equals(RecentAudioCachePolicy.pressure(4,40L*mb)),"no false eviction");
  System.out.println("PASS: "+checks+" bounded replay cache policy checks");
 }
}
