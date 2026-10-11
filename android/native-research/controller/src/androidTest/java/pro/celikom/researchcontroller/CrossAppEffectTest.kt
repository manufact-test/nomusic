package pro.celikom.researchcontroller

import android.content.BroadcastReceiver
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.audiofx.AudioEffect
import android.media.MediaPlayer
import android.media.AudioManager
import android.media.audiofx.DynamicsProcessing
import android.media.audiofx.Visualizer
import android.os.Build
import android.os.Process
import android.os.SystemClock
import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.core.content.ContextCompat
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.atomic.AtomicReference
import kotlin.math.sqrt

@RunWith(AndroidJUnit4::class)
class CrossAppEffectTest {
    @Test fun classifyExternalSessionAttenuation() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val state = AtomicReference<Intent>()
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) { state.set(intent) }
        }
        ContextCompat.registerReceiver(context, receiver,
            IntentFilter("pro.celikom.research.SNAPSHOT"), ContextCompat.RECEIVER_EXPORTED)
        var effect: DynamicsProcessing? = null
        var visualizer: Visualizer? = null
        var alternate: MediaPlayer? = null
        var alternateVisualizer: Visualizer? = null
        val audioManager = context.getSystemService(AudioManager::class.java)
        val oldVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC)
        val report = JSONObject().put("api", Build.VERSION.SDK_INT)
            .put("yandex_tested", false).put("physical_routes_tested", false)
        try {
            context.startActivity(Intent().setComponent(ComponentName(
                "pro.celikom.researchsource", "pro.celikom.researchsource.SourceActivity"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            val deadline = SystemClock.elapsedRealtime() + 5000
            while (state.get() == null && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(50)
            val initial = requireNotNull(state.get()) { "Owned source did not report" }
            assertNotEquals(Process.myUid(), initial.getIntExtra("uid", -1))
            assertTrue(initial.getBooleanExtra("playing", false))
            val session = initial.getIntExtra("session", 0)
            assertTrue(session > 0)
            report.put("distinct_uids", true).put("session_nonzero", true)
            // Owned emulator only. Low default stream gain can quantize quiet 8-bit samples to zero.
            audioManager.setStreamVolume(AudioManager.STREAM_MUSIC,
                audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC), 0)
            report.put("measurement_stream_volume", audioManager.getStreamVolume(AudioManager.STREAM_MUSIC))
            report.put("effects", AudioEffect.queryEffects().map { it.name }.joinToString(";"))
            instrumentation.uiAutomation.grantRuntimePermission(context.packageName,
                "android.permission.RECORD_AUDIO")
            // Session-local waveform only: controlled, owned sine. Never service content.
            visualizer = Visualizer(session).apply {
                captureSize = Visualizer.getCaptureSizeRange()[1]
                scalingMode = Visualizer.SCALING_MODE_AS_PLAYED
                enabled = true
            }
            val before = rms(visualizer)
            report.put("baseline_rms", before)
            assertTrue("Owned baseline must be measurable", before > 0.5)
            alternate = MediaPlayer.create(context, pro.celikom.researchcontroller.R.raw.alternate)
                .apply { isLooping = true; start() }
            assertNotEquals(session, alternate.audioSessionId)
            alternateVisualizer = Visualizer(alternate.audioSessionId).apply {
                captureSize = Visualizer.getCaptureSizeRange()[1]
                scalingMode = Visualizer.SCALING_MODE_AS_PLAYED
                enabled = true
            }
            val alternateBefore = rms(alternateVisualizer)
            assertTrue("Separate alternative must be measurable", alternateBefore > 0.5)
            effect = DynamicsProcessing(0, session, null)
            assertTrue("Effect must be controlled", effect.hasControl())
            effect.setInputGainAllChannelsTo(-100f)
            assertEquals(AudioEffect.SUCCESS, effect.setEnabled(true))
            val muted = rms(visualizer)
            val alternateDuring = rms(alternateVisualizer)
            val position = state.get().getIntExtra("position", -1)
            SystemClock.sleep(400)
            assertTrue(state.get().getBooleanExtra("playing", false))
            assertTrue(state.get().getIntExtra("position", -1) != position)
            report.put("effect_attached", true).put("attenuated_rms", muted)
                .put("source_keeps_playing", true)
                .put("alternate_before_rms", alternateBefore)
                .put("alternate_during_rms", alternateDuring)
                .put("alternate_unaffected", alternateDuring > alternateBefore * 0.5)
            effect.release()
            effect = null
            val restored = rms(visualizer)
            report.put("restored_rms", restored)
            // A successful setter alone does not establish audible attenuation.
            report.put("measured_attenuation", muted < before * 0.1)
                .put("measured_restore", restored > before * 0.5)
                .put("classification", if (muted < before * 0.1 && restored > before * 0.5
                    && alternateDuring > alternateBefore * 0.5)
                    "owned_cross_app_candidate" else "effect_not_proven_by_waveform")
        } catch (failure: RuntimeException) {
            // Unsupported effects/permissions are research outcomes, not integration PASS.
            report.put("classification", "unsupported_or_denied")
                .put("error_type", failure.javaClass.simpleName)
                .put("error", failure.message?.take(180))
        } finally {
            effect?.release()
            visualizer?.release()
            alternateVisualizer?.release()
            alternate?.release()
            audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, oldVolume, 0)
            context.unregisterReceiver(receiver)
            instrumentation.uiAutomation.executeShellCommand(
                "am force-stop pro.celikom.researchsource").close()
            Log.i("CELIKOM_NATIVE_RESEARCH", report.toString())
        }
    }
    private fun rms(visualizer: Visualizer): Double {
        SystemClock.sleep(400)
        val data = ByteArray(visualizer.captureSize)
        var total = 0.0
        repeat(8) {
            assertEquals(Visualizer.SUCCESS, visualizer.getWaveForm(data))
            total += sqrt(data.sumOf { sample ->
                val value = (sample.toInt() and 255) - 128
                (value * value).toDouble()
            } / data.size)
            SystemClock.sleep(60)
        }
        return total / 8
    }
}
