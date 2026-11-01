package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;
import org.json.JSONObject;
import java.io.File;

/** Locks the owner-approved 0.3.78 local-cache start and seek behavior.
 * This is an actual ReplacementEngine replay, not a hardware-output measurement.
 */
public final class TestCachedAudioRollback {
  static int checks;
  static int initialSeekCount;

  static void check(boolean value, String reason) {
    checks++;
    if (!value) throw new AssertionError(reason);
  }

  static MediaPlayer startCached() throws Exception {
    TestEngine.reset("ALBUM");
    ReplacementEngine engine = TestEngine.e;
    engine.arm();

    JSONObject approved = TestEngine.found();
    File cached = File.createTempFile("celikom-cache-rollback-", ".audio");
    engine.recentAudio.put(engine.audioKey(approved), cached);
    TestEngine.resolve();

    check(TestEngine.api.resolves == 1,
        "cached audio reuse still requires a fresh live resolve");
    check(engine.player != null && engine.audioFile == cached
            && engine.streaming == null && TestEngine.api.downloads == 0,
        "the validated local cache hit creates a local-file decoder without stream or download");

    MediaPlayer decoder = engine.player;
    decoder.prepared.onPrepared(decoder);

    check(decoder.playing && engine.fading,
        "prepared local cache starts the existing complementary entry");
    check(!engine.audioOwner.handoverAwaitingClock(),
        "0.3.78 cache hit must not acquire the extra streaming cold-decoder gate");
    initialSeekCount = decoder.seekCalls;
    return decoder;
  }

  static void advanceTogether(MediaPlayer decoder, int ticks, long tickMs) {
    long sourcePosition = TestEngine.p.current.position;
    for (int i = 0; i < ticks; i++) {
      SystemClock.now += tickMs;
      decoder.position += tickMs;
      sourcePosition += tickMs;
      TestEngine.p.current = TestEngine.source("1", sourcePosition, true);
      TestEngine.p.handler.drain();
    }
  }

  static void cachedStartRemainsOnTheApprovedPath() throws Exception {
    MediaPlayer decoder = startCached();
    ReplacementEngine engine = TestEngine.e;

    advanceTogether(decoder, 10, 20);

    check(!engine.fading
            && engine.audioOwner.state() == AudioOwnership.State.REPLACEMENT
            && decoder.volume > 0.99f
            && engine.effect != null
            && engine.effect.gain == -100f,
        "local cache completes the existing 160ms complementary entry without a cold gate");
    check(decoder.seekCalls == initialSeekCount,
        "local cache startup does not add a post-attach WARM correction");
    engine.close();
  }

  static void cachedUserSeekRetainsTheSameDecoder() throws Exception {
    MediaPlayer decoder = startCached();
    ReplacementEngine engine = TestEngine.e;
    advanceTogether(decoder, 10, 20);

    DynamicsProcessing sourceEffect = engine.effect;
    int beforeSeek = decoder.seekCalls;
    decoder.asyncSeek = true;
    engine.sourceSeekRequested();
    TestEngine.p.current = TestEngine.source("1", 60000, true);
    engine.update(TestEngine.p.current);

    check(engine.seeking
            && decoder.seekCalls == beforeSeek + 1
            && !decoder.playing
            && decoder.volume == 0f
            && engine.effect == sourceEffect
            && sourceEffect.gain == 0f
            && engine.originalMix == 1f,
        "cached user seek keeps the original audible and holds the same replacement decoder");

    SystemClock.now += 65;
    TestEngine.p.current = TestEngine.source("1", 60065, true);
    decoder.seek.onSeekComplete(decoder);

    check(!engine.seeking
            && decoder.playing
            && engine.player == decoder
            && engine.effect == sourceEffect
            && decoder.seekCalls == beforeSeek + 1,
        "cached seek resumes the same decoder after one accepted alignment callback");

    advanceTogether(decoder, 8, 250);
    check(engine.player == decoder
            && decoder.playing
            && decoder.seekCalls == beforeSeek + 1
            && engine.effect == sourceEffect
            && decoder.volume > 0.99f
            && sourceEffect.gain == -100f,
        "stable playback after cached seek creates no redundant audible reseek");
    engine.close();
  }

  public static void main(String[] args) throws Exception {
    cachedStartRemainsOnTheApprovedPath();
    cachedUserSeekRetainsTheSameDecoder();
    System.out.println("PASS: " + checks
        + " cached local-file startup and same-decoder seek rollback checks");
  }
}
