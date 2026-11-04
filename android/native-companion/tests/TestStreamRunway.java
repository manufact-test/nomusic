package pro.celikom.nativeprobe.identitydiag;

import java.io.File;
import java.io.IOException;

/** Test.32: scattered sparse data cannot acquire audible ownership. */
public final class TestStreamRunway {
 static int checks;
 static void check(boolean yes,String reason){checks++;if(!yes)throw new AssertionError(reason);}
 public static void main(String[] args)throws Exception{
  BufferedAudio audio=new BufferedAudio(File.createTempFile("runway-test-",".mp3"),
   ()->{throw new IOException("offline test");},()->true,()->0L,(name,bytes)->{});
  try{
   audio.size=BufferedAudio.BLOCK*24L;
   audio.present.set(0);audio.present.set(23);
   for(int n=12;n<24;n++)audio.present.set(n);
   check(audio.cachedBytes()>BufferedAudio.BLOCK*12L,
     "large scattered cache is not a usable beginning");
   check(!audio.hasPlayableRunway(0,120000),
     "valid footer and second-half cache never qualify first seconds");
   for(int n=1;n<3;n++)audio.present.set(n);
   check(!audio.hasPlayableRunway(0,120000),
     "three prefix blocks cannot authorize the minimum future runway");
   for(int n=3;n<8;n++)audio.present.set(n);
   check(audio.hasPlayableRunway(0,120000),
     "verified contiguous first megabyte passes the bounded runway gate");
   check(!audio.hasPlayableRunway(40000,120000),
     "future source position is checked at its own decoder neighborhood");
   audio.present.set(8,12);
   check(audio.hasPlayableRunway(40000,120000),
     "verified continuous middle neighborhood qualifies without full download");
   audio.present.set(0,audio.blocks());
   check(audio.complete()&&audio.hasPlayableRunway(112000,120000),
     "fully cached source always qualifies including the tail");
  }finally{audio.close();}
  System.out.println("PASS: "+checks+" Test.32 verified contiguous sparse runway checks");
 }
}
