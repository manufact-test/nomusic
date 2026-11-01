package pro.celikom.nativeprobe.identitydiag;

import android.media.MediaPlayer;
import android.os.SystemClock;
import org.json.JSONObject;
import java.io.File;

/** Regression for a validated local cache hit: it creates a NEW MediaPlayer,
 * and that decoder must pass the same motion/clock gate as a range stream.
 * Transport clocks are not PCM or hardware-output measurements.
 */
public final class TestCachedDecoderJoin {
  static int checks;
  static void check(boolean value, String reason) {
    checks++;
    if (!value) throw new AssertionError(reason);
  }

  static MediaPlayer startCached() throws Exception {
    TestEngine.reset("ALBUM");
    ReplacementEngine engine = TestEngine.e;
    engine.arm();
    JSONObject approved = TestEngine.found();
    File cached = File.createTempFile("celikom-cached-join-", ".audio");
    engine.recentAudio.put(engine.audioKey(approved), cached);
    TestEngine.resolve();

    check(TestEngine.api.resolves == 1,
        "cached audio reuse still requires a fresh live resolve");
    check(engine.player != null && engine.audioFile == cached
            && engine.streaming == null && TestEngine.api.downloads == 0,
        "cache hit uses the validated local file without a new stream or download");

    MediaPlayer decoder = engine.player;
    decoder.prepared.onPrepared(decoder);
    check(decoder.playing && engine.fading,
        "cache hit creates and starts a fresh decoder in the muted handover phase");
    return decoder;
  }

  static void delayedStartupKeepsOriginal() throws Exception {
    MediaPlayer decoder = startCached();
    ReplacementEngine engine = TestEngine.e;

    check(engine.audioOwner.handoverAwaitingClock(),
        "local cache hit must acquire the same decoder-motion gate as streaming");

    SystemClock.now += 500;
    TestEngine.p.current = TestEngine.source("1", 1500, true);
    TestEngine.p.handler.drain();
    check(engine.audioOwner.handoverAwaitingClock()
            && engine.originalMix == 1f
            && decoder.volume == 0f
            && engine.effect != null
            && engine.effect.gain == 0f,
        "a playing-but-frozen cached decoder cannot attenuate the original or gain output");

    SystemClock.now += 1600;
    TestEngine.p.current = TestEngine.source("1", 3100, true);
    TestEngine.p.handler.drain();
    check(engine.player == null && decoder.released
            && engine.effect == null && engine.armed(),
        "a cached decoder that never advances fails open to the original");

    check(TestEngine.api.downloads == 0,
        "cached decoder startup failure does not silently fall through to a download");
    engine.close();
  }

  static void cachedPathUsesExistingWarmSyncGate() throws Exception {
    MediaPlayer decoder = startCached();
    ReplacementEngine engine = TestEngine.e;
    decoder.asyncSeek = true;

    SystemClock.now += 50;
    decoder.position += 50;
    TestEngine.p.current = TestEngine.source("1", 1200, true);
    TestEngine.p.handler.drain();

    check(engine.audioOwner.seekInFlight(decoder)
            && decoder.seekCalls == 2
            && decoder.position == 1270
            && decoder.volume == 0f
            && engine.originalMix == 1f
            && engine.effect != null
            && engine.effect.gain == 0f,
        "cache hit uses the existing muted 70ms WARM correction while original remains audible");

    SystemClock.now += 50;
    TestEngine.p.current = TestEngine.source("1", 1250, true);
    decoder.seek.onSeekComplete(decoder);
    SystemClock.now += 50;
    decoder.position += 50;
    TestEngine.p.current = TestEngine.source("1", decoder.position, true);
    TestEngine.p.handler.drain();

    check(!engine.audioOwner.handoverAwaitingClock()
            && !engine.audioOwner.seekInFlight(decoder)
            && engine.audioOwner.state() == AudioOwnership.State.SAME_SONG_BLEND,
        "cache path validates decoder motion and corrected transport drift before joining");

    SystemClock.now += 200;
    decoder.position += 200;
    TestEngine.p.current = TestEngine.source("1", decoder.position, true);
    TestEngine.p.handler.drain();
    check(!engine.fading
            && engine.originalMix == 0f
            && decoder.volume == 1f
            && engine.audioOwner.state() == AudioOwnership.State.REPLACEMENT,
        "verified cached decoder completes the existing complementary join");
    engine.close();
  }

  public static void main(String[] args) throws Exception {
    delayedStartupKeepsOriginal();
    cachedPathUsesExistingWarmSyncGate();
    System.out.println("PASS: " + checks
        + " cached-file decoder motion, warm alignment and fail-open checks");
  }
}
