package pro.celikom.nativeprobe

import android.media.AudioTrack
import android.media.AudioAttributes
import android.media.AudioFormat
import org.json.JSONObject
import kotlin.math.PI
import kotlin.math.sin

/** Finite quiet local signal, in a different session from the Yandex effect. */
class TestTone(private val sourceSession: Int) {
    private var track: AudioTrack? = null
    private var session = -1
    private var frames = 0
    private var submitted = 0
    fun start() {
        val samples = ShortArray(16000 * 7) { index ->
            val phase = index % 8000
            val ramp = minOf(1.0, phase / 320.0, (6400-phase).coerceAtLeast(0) / 320.0)
            val frequency = if ((index / 8000) % 2 == 0) 440.0 else 660.0
            (1200 * ramp * sin(2 * PI * frequency * index / 16000)).toInt().toShort()
        }
        val candidate = AudioTrack.Builder().setAudioAttributes(AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
            .setAudioFormat(AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(16000).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
            .setTransferMode(AudioTrack.MODE_STATIC).setBufferSizeInBytes(samples.size*2).build()
        track = candidate
        session = candidate.audioSessionId
        check(session > 0 && session != sourceSession)
        submitted = candidate.write(samples, 0, samples.size)
        check(submitted == samples.size && candidate.state == AudioTrack.STATE_INITIALIZED)
        candidate.play()
    }
    fun snapshot(): JSONObject {
        try { track?.let { frames = it.playbackHeadPosition } } catch (_: RuntimeException) { }
        return JSONObject().put("source", "local_test_tone").put("audio_session_id", session)
            .put("different_from_yandex_session", session > 0 && session != sourceSession)
            .put("submitted_frames", submitted).put("played_frames", frames).put("sample_rate", 16000)
            .put("focus_requested", false)
    }
    fun release(): Boolean {
        snapshot()
        var released = true
        track?.let { try { it.stop() } catch (_: RuntimeException) { }; try { it.release() } catch (_: RuntimeException) { released = false } }
        track = null
        return released
    }
}
