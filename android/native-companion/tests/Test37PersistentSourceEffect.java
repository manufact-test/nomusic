package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import pro.celikom.nativeprobe.AttenuationService;
import java.io.File;

/** Test.37 isolates the session DSP lifecycle; it makes no acoustic claims. */
public final class Test37PersistentSourceEffect {
 static int assertions;
 static void check(boolean yes,String why){assertions++;if(!yes)throw new AssertionError(why);}

 static void nextSong(String alias,String trackId)throws Exception{
  ReplacementEngine e=TestEngine.e;
  TestEngine.p.current=TestEngine.source(alias,1000,true);
  e.identity(LogStore.map("mediaAlias",alias,"albumId","42","title","Песня",
    "artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId",trackId,"method","ALBUM"));
  TestEngine.resolve();
  File file=File.createTempFile("celikom-test37-", ".audio");
  TestEngine.api.downloaded.done(file,null);
  MediaPlayer decoder=e.player;
  check(decoder!=null,"new track decoder must pass a fresh live resolve");
  decoder.prepared.onPrepared(decoder);
  check(e.effect!=null&&e.effect.getEnabled(),"new track has a verified current effect");
 }

 static void reuseAcrossConfirmedBoundaries()throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;
  DynamicsProcessing first=e.effect;int constructed=DynamicsProcessing.constructionCount;
  int enabled=DynamicsProcessing.enabledCount;
  MediaPlayer previous=e.player;
  e.sourceBoundary("confirmed_manual_next","2");
  check(previous.released&&!previous.playing&&previous.volume==0f&&e.effect==null,
    "boundary must retire old decoder and active output lease");
  check(e.parkedSourceEffect==first&&first.getEnabled()&&!first.released&&first.gain==0f,
    "same-session effect stays attached but source is audible at unity");
  nextSong("2","8");
  check(e.effect==first&&e.parkedSourceEffect==null&&e.originalMix==1f,
    "second track adopts the same effect from a fresh catalogue resolve");
  check(DynamicsProcessing.constructionCount==constructed&&DynamicsProcessing.enabledCount==enabled,
    "second track must not create, enable or toggle the Android effect");
  e.sourceBoundary("confirmed_auto_next","3");
  nextSong("3","9");
  check(e.effect==first&&DynamicsProcessing.constructionCount==constructed
      &&DynamicsProcessing.enabledCount==enabled,
    "third song reuses the same effect without a DSP install cycle");
  e.stop("owner_stop");
  check(first.released&&e.parkedSourceEffect==null&&e.effect==null&&!e.armed(),
    "stop fully releases source effect and decoder");
 }

 static void routeLossWhileParked()throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;
  DynamicsProcessing original=e.effect;
  e.sourceBoundary("confirmed_next","2");
  e.headphonesDisconnected();
  check(original.released&&e.parkedSourceEffect==null&&e.effect==null,
    "route loss releases parked effect before any resume");
  e.close();
 }

 static void accountSwitchWhileParked()throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;
  DynamicsProcessing original=e.effect;
  e.sourceBoundary("confirmed_next","2");
  TestEngine.api.accountGeneration++;
  e.update(TestEngine.source("2",1000,true));
  check(original.released&&e.parkedSourceEffect==null&&!e.armed(),
    "account change revokes the parked source effect immediately");
  e.close();
 }

 static void sessionChangeWhileParked()throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;
  DynamicsProcessing original=e.effect;
  e.sourceBoundary("confirmed_next","2");
  AttenuationService.Companion.session=303;
  nextSongAfterSessionChange(e);
  check(original.released&&e.parkedSourceEffect==null&&!e.armed(),
    "fresh session mismatch must not reuse an effect attached to an old session");
  e.close();
 }
 static void nextSongAfterSessionChange(ReplacementEngine e)throws Exception{
  TestEngine.p.current=TestEngine.source("2",1000,true);
  e.identity(LogStore.map("mediaAlias","2","albumId","42","title","Песня",
    "artist","Артист","durationMs",120000L),
    LogStore.map("candidateTrackId","8","method","ALBUM"));
  TestEngine.resolve();
  File file=File.createTempFile("celikom-test37-session-", ".audio");
  TestEngine.api.downloaded.done(file,null);
  if(e.player!=null&&e.player.prepared!=null)e.player.prepared.onPrepared(e.player);
 }

 static void parkedControlLoss()throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;
  DynamicsProcessing original=e.effect;
  e.sourceBoundary("confirmed_next","2");
  original.listener.onControlStatusChange(original,false);
  check(!e.armed()&&original.released&&e.parkedSourceEffect==null,
    "control loss must revoke a parked effect even when no decoder is active");
  e.close();
 }

 static void sameTrackSeekKeepsItsExistingEffect()throws Exception{
  TestEngine.playing();ReplacementEngine e=TestEngine.e;
  DynamicsProcessing original=e.effect;
  int constructors=DynamicsProcessing.constructionCount;
  TestEngine.p.current=TestEngine.source("1",60000,true);
  e.update(TestEngine.p.current);
  check(e.effect==original&&e.parkedSourceEffect==null
     &&DynamicsProcessing.constructionCount==constructors,
    "same-item seek retains its current DSP, without a new parked lease");
  e.close();
 }

 public static void main(String[] args)throws Exception{
  reuseAcrossConfirmedBoundaries();routeLossWhileParked();accountSwitchWhileParked();
  sessionChangeWhileParked();parkedControlLoss();sameTrackSeekKeepsItsExistingEffect();
  System.out.println("PASS: "+assertions+" Test.37 persistent session DSP lifecycle assertions");
 }
}
