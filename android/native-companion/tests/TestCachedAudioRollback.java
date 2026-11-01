package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.media.audiofx.DynamicsProcessing;
import android.os.SystemClock;
import org.json.JSONObject;
import java.io.File;

/** Exercises muted local-file prewarm, bounded clock validation, original fallback and unchanged manual seek behavior. */
public final class TestCachedAudioRollback {
  static int checks;
  static int initialSeekCount;

  static void check(boolean value, String reason) {
    checks++;
    if (!value) throw new AssertionError(reason);
  }

  static void advanceWarmup(MediaPlayer decoder, int ticks, long tickMs, int decoderStartsAtTick) {
    long sourcePosition = TestEngine.p.current.position;
    for (int i = 0; i < ticks; i++) {
      SystemClock.now += tickMs;
      sourcePosition += tickMs;
      if (i >= decoderStartsAtTick) decoder.position += tickMs;
      TestEngine.p.current = TestEngine.source("1", sourcePosition, true);
      TestEngine.p.handler.drain();
    }
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

  static MediaPlayer startCached(boolean finishWarmup) throws Exception {
    TestEngine.reset("ALBUM");
    TestEngine.p.current = TestEngine.source("1", 100, true);
    ReplacementEngine engine = TestEngine.e;
    engine.arm();

    JSONObject approved = TestEngine.found();
    File cached = File.createTempFile("celikom-cache-prewarm-", ".audio");
    engine.recentAudio.put(engine.audioKey(approved), cached);
    TestEngine.resolve();

    check(TestEngine.api.resolves == 1,
        "cached audio reuse still requires a fresh live resolve");
    check(engine.player != null && engine.audioFile == cached
            && engine.streaming == null && TestEngine.api.downloads == 0,
        "the validated local cache hit creates a new local-file decoder without stream or download");

    MediaPlayer decoder = engine.player;
    decoder.prepared.onPrepared(decoder);

    check(decoder.playing && engine.localPrewarmWarmupPending && !engine.fading,
        "local-file decoder is started muted before initial alignment");
    check(decoder.volume == 0f && engine.effect != null && engine.effect.gain == 0f
            && engine.originalMix == 1f && !engine.audioOwner.handoverAwaitingClock(),
        "original remains fully audible and replacement silent throughout decoder warmup");
    check(decoder.startCalls == 1 && decoder.pauseCalls == 0 && decoder.seekCalls == 0,
        "decoder warmup starts before the first alignment seek and does not pause the decoder");
    check(engine.audioFromCache,
        "the reused object is a cached audio file, not a cached MediaPlayer decoder");

    if (finishWarmup) {
      // Reproduce the observed local MediaPlayer startup delay: source advances
      // while the muted decoder clock initially remains stationary.
      advanceWarmup(decoder, 10, 20, 8);
      check(!engine.localPrewarmWarmupPending && engine.fading
              && engine.audioOwner.handoverAwaitingClock()
              && decoder.seekCalls == 1 && decoder.pauseCalls == 0
              && decoder.volume == 0f && engine.effect.gain == 0f,
          "after muted decoder motion, align while it is already running and keep original audible through the join gate");
    }

    initialSeekCount = decoder.seekCalls;
    return decoder;
  }

  static MediaPlayer startCached() throws Exception {
    return startCached(true);
  }

  static void cachedStartUsesPrewarmedClock() throws Exception {
    MediaPlayer decoder = startCached();
    ReplacementEngine engine = TestEngine.e;

    advanceTogether(decoder, 10, 20);

    check(!engine.fading
            && engine.audioOwner.state() == AudioOwnership.State.REPLACEMENT
            && decoder.volume > 0.99f
            && engine.effect != null
            && engine.effect.gain == -100f,
        "prewarmed local cache completes the existing 160ms complementary entry after clock validation");
    check(decoder.seekCalls == initialSeekCount,
        "prewarmed local cache reaches handover without a post-attach WARM correction");
    engine.close();
  }

  static void cachedPrewarmTimeoutKeepsOriginal() throws Exception {
    MediaPlayer decoder = startCached(false);
    ReplacementEngine engine = TestEngine.e;

    SystemClock.now += ReplacementEngine.SEEK_TIMEOUT_MS + 1;
    TestEngine.p.handler.drain();

    check(engine.player == null && decoder.released && engine.effect == null
            && engine.audioOwner.state() == AudioOwnership.State.TRACK_UNSUPPORTED
            && engine.completedReason != null
            && engine.completedReason.contains("Синхронизация неустойчива"),
        "a local decoder that never advances is rejected and the original remains the only output");
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
            && decoder.pauseCalls > 0
            && !decoder.playing
            && decoder.volume == 0f
            && engine.effect == sourceEffect
            && sourceEffect.gain == 0f
            && engine.originalMix == 1f,
        "manual cached seek keeps the original audible and pauses the same replacement decoder");

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
    cachedStartUsesPrewarmedClock();
    cachedPrewarmTimeoutKeepsOriginal();
    cachedUserSeekRetainsTheSameDecoder();
    System.out.println("PASS: " + checks
        + " cached local-file prewarm, safe fallback and same-decoder seek checks");
  }
}
