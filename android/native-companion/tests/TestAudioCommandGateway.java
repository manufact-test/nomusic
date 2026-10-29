package pro.celikom.nativeprobe.identitydiag;
import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
/** No duplicate command paths may start, seek or unmute a retired decoder. */
public final class TestAudioCommandGateway {
 static int checks;
 static void ok(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
 interface Action { void run(); }
 static void rejected(Action action,String why){
  boolean failed=false;try{action.run();}catch(IllegalStateException expected){failed=true;}
  ok(failed,why);
 }
 public static void main(String[] args)throws Exception {
  AudioOwnership owner=new AudioOwnership();owner.track("first");
  long generation=owner.epoch();MediaPlayer decoder=new MediaPlayer();
  DynamicsProcessing effect=new DynamicsProcessing(0,101,null);
  rejected(()->owner.startDecoder(decoder,effect,"first",generation),"source only cannot start secondary decoder");
  owner.prepareSourceEffect(effect);owner.volume(decoder,0f,null);owner.startDecoder(decoder,effect,"first",generation);
  ok(decoder.playing&&decoder.volume==0f,"preparing decoder runs silently");
  rejected(()->owner.seekDecoder(decoder,3000,"first",generation),"preparation without alignment cannot seek audibly");
  owner.aligning();owner.seekDecoder(decoder,1000,"first",generation);
  ok(decoder.seekCalls==1,"silent alignment seeks current decoder");
  owner.grantReplacement(effect);owner.volume(decoder,1f,effect);
  int gainWrites=effect.gainWrites,volumeWrites=decoder.volumeWrites;
  for(int poll=0;poll<80;poll++){owner.grantReplacement(effect);owner.volume(decoder,1f,effect);}
  ok(effect.gainWrites==gainWrites,"steady playback does not rewrite original effect gain");
  ok(decoder.volumeWrites==volumeWrites,"steady playback does not rewrite decoder volume");
  rejected(()->owner.seekDecoder(decoder,5000,"first",generation),"audible decoder cannot seek without silencing");
  owner.volume(decoder,0f,effect);owner.aligning();
  owner.seekDecoder(decoder,5000,"first",generation);
  ok(decoder.position==5000,"muted decoder may resynchronize");
  owner.pauseDecoder(decoder);ok(!decoder.playing,"pause command always silences safely");
  owner.restoreSource(decoder,effect);owner.invalidate("media3_boundary");
  rejected(()->owner.startDecoder(decoder,effect,"first",generation),"stale callback cannot restart previous song");
  rejected(()->owner.seekDecoder(decoder,100,"first",generation),"stale callback cannot seek previous song");
  owner.stopped();owner.track("other");
  rejected(()->owner.startDecoder(decoder,effect,"other",owner.epoch()),"stopped service cannot reanimate");
  System.out.println("PASS: "+checks+" exclusive transport command gateway checks");
 }
}
